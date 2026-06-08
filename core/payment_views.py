"""Premium payment experience + Razorpay integration."""

import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.conf import settings

from .models import Booking, Payment, Invoice
from .views import get_custom_user_from_request
from .provider_utils import get_provider_from_session, get_booking_amount
from .payment_utils import (
    RAZORPAY_ONLINE_MODES,
    get_or_create_pending_payment,
    create_razorpay_order,
    verify_razorpay_signature,
    complete_payment,
    booking_has_completed_payment,
    create_invoice_for_booking,
)
from .tasks import send_payment_receipt_email, send_invoice_email_task


def _get_user_booking(request, booking_id):
    user = get_custom_user_from_request(request)
    if not user:
        return None, None
    booking = get_object_or_404(
        Booking.objects.select_related('user', 'provider', 'service').prefetch_related('payments'),
        id=booking_id, user=user,
    )
    return user, booking


@require_GET
def payment_checkout(request, booking_id):
    """Premium payment checkout page."""
    user, booking = _get_user_booking(request, booking_id)
    if not user:
        return redirect('login')

    if booking_has_completed_payment(booking):
        messages.info(request, 'This booking is already paid.')
        return redirect('payment_history')

    amount = get_booking_amount(booking)
    latest_payment = booking.payments.order_by('-id').first()

    return render(request, 'payment/checkout.html', {
        'booking': booking,
        'amount': amount,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'latest_payment': latest_payment,
        'online_modes': RAZORPAY_ONLINE_MODES,
    })


@require_POST
def create_razorpay_order_api(request, booking_id):
    """Create Razorpay order for online payment modes."""
    user, booking = _get_user_booking(request, booking_id)
    if not user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        body = json.loads(request.body.decode('utf-8'))
        mode = body.get('mode', 'googlepay')
    except json.JSONDecodeError:
        mode = request.POST.get('mode', 'googlepay')

    amount = get_booking_amount(booking)
    payment, err = get_or_create_pending_payment(booking, amount, mode=mode)
    if err:
        return JsonResponse({'error': err}, status=400)

    try:
        order = create_razorpay_order(payment)
    except Exception as exc:
        return JsonResponse({'error': f'Razorpay error: {exc}'}, status=500)

    return JsonResponse({
        'order_id': order['id'],
        'amount': int(amount * 100),
        'currency': 'INR',
        'key': settings.RAZORPAY_KEY_ID,
        'payment_id': payment.id,
        'booking_id': booking.id,
        'customer_name': user.name,
        'customer_email': user.email,
        'customer_phone': user.phone or '',
    })


@require_POST
def verify_razorpay_payment_api(request):
    """Verify Razorpay signature and mark payment completed."""
    user = get_custom_user_from_request(request)
    if not user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    order_id = data.get('razorpay_order_id')
    payment_id_rzp = data.get('razorpay_payment_id')
    signature = data.get('razorpay_signature')
    local_payment_id = data.get('payment_id')

    if not all([order_id, payment_id_rzp, signature, local_payment_id]):
        return JsonResponse({'error': 'Missing payment fields'}, status=400)

    payment = get_object_or_404(Payment, id=local_payment_id, booking__user=user)

    if payment.status == 'completed':
        return JsonResponse({'success': True, 'message': 'Already verified'})

    if not verify_razorpay_signature(order_id, payment_id_rzp, signature):
        payment.status = 'failed'
        payment.save(update_fields=['status', 'updated_at'])
        return JsonResponse({'error': 'Payment verification failed'}, status=400)

    complete_payment(payment, payment_id_rzp, signature)
    send_payment_receipt_email.delay(payment.id)

    return JsonResponse({
        'success': True,
        'transaction_id': payment.transaction_id,
        'redirect': '/payment/history/',
    })


@require_GET
def payment_history(request):
    """Customer payment history with filters."""
    user = get_custom_user_from_request(request)
    if not user:
        return redirect('login')

    payments = Payment.objects.filter(booking__user=user).select_related(
        'booking', 'booking__service', 'booking__provider',
    )

    status_filter = request.GET.get('status', '')
    if status_filter in ('completed', 'pending', 'failed'):
        payments = payments.filter(status=status_filter)

    sort = request.GET.get('sort', 'latest')
    if sort == 'oldest':
        payments = payments.order_by('created_at')
    else:
        payments = payments.order_by('-created_at')

    q = request.GET.get('q', '').strip()
    if q:
        from django.db.models import Q
        payments = payments.filter(
            Q(transaction_id__icontains=q)
            | Q(booking__service__name__icontains=q)
            | Q(razorpay_payment_id__icontains=q)
        )

    return render(request, 'payment/history.html', {
        'payments': payments,
        'status_filter': status_filter,
        'sort': sort,
        'q': q,
    })


def _can_view_invoice(request, invoice):
    user = get_custom_user_from_request(request)
    provider = get_provider_from_session(request)
    if user and invoice.booking.user_id == user.id:
        return True
    if provider and invoice.booking.provider_id == provider.id:
        return True
    if hasattr(request, 'user') and request.user.is_staff:
        return True
    return False


@require_GET
def view_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice.objects.select_related('booking'), id=invoice_id)
    if not _can_view_invoice(request, invoice):
        raise Http404
    return render(request, 'payment/invoice_detail.html', {'invoice': invoice})


@require_GET
def download_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if not _can_view_invoice(request, invoice):
        raise Http404
    if not invoice.pdf_file:
        raise Http404
    return FileResponse(invoice.pdf_file.open('rb'), as_attachment=True, filename=f'{invoice.invoice_number}.pdf')
