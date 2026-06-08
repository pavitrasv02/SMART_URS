"""Provider dashboard helpers: auth, earnings, emails."""

from functools import wraps
from decimal import Decimal

from django.shortcuts import redirect
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .models import ServiceProvider, Booking, Payment, Review


def get_provider_from_session(request):
    """Load provider from session without availability filter (chat, invoices)."""
    provider_id = request.session.get('provider_id')
    if not provider_id:
        return None
    try:
        return ServiceProvider.objects.get(id=provider_id)
    except ServiceProvider.DoesNotExist:
        request.session.pop('provider_id', None)
        return None


def get_provider_from_request(request):
    provider = get_provider_from_session(request)
    if provider and not provider.availability:
        return None
    return provider


def provider_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not get_provider_from_request(request):
            return redirect('provider_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def provider_session_required(view_func):
    """Provider session check without availability filter — used for chat."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not get_provider_from_session(request):
            return redirect('provider_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_provider_bookings(provider):
    return Booking.objects.filter(provider=provider).select_related('user', 'service')


def get_booking_amount(booking):
    payment = booking.payments.filter(status='completed').first()
    if payment:
        return payment.amount
    if booking.total_amount:
        return booking.total_amount
    if booking.total_price and booking.total_price > 0:
        return booking.total_price
    if booking.service:
        return booking.service.base_price
    return Decimal('1500.00')


def get_provider_earnings(provider):
    completed = Payment.objects.filter(
        booking__provider=provider,
        booking__status='Completed',
        status='completed',
    )
    now = timezone.now()
    today = now.date()
    total = completed.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    today_total = completed.filter(
        Q(paid_at__date=today) | Q(paid_at__isnull=True, created_at__date=today)
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    monthly_total = completed.filter(
        Q(paid_at__year=now.year, paid_at__month=now.month)
        | Q(paid_at__isnull=True, created_at__year=now.year, created_at__month=now.month)
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    from datetime import timedelta
    week_start = today - timedelta(days=today.weekday())
    weekly_total = completed.filter(
        Q(paid_at__date__gte=week_start) | Q(paid_at__isnull=True, created_at__date__gte=week_start)
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    return {
        'today': today_total,
        'weekly': weekly_total,
        'monthly': monthly_total,
        'total': total,
    }


def get_provider_rating_stats(provider):
    reviews = Review.objects.filter(booking__provider=provider)
    total = reviews.count()
    avg = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    breakdown = {i: 0 for i in range(1, 6)}
    for row in reviews.values('rating').annotate(count=Count('id')):
        breakdown[row['rating']] = row['count']
    return {
        'average': round(avg, 1),
        'total': total,
        'stars': breakdown,
    }


def get_provider_analytics(provider):
    bookings = get_provider_bookings(provider)
    assigned = bookings.count()
    completed = bookings.filter(status='Completed').count()
    completion_rate = round((completed / assigned * 100), 1) if assigned else 0

    monthly_bookings = list(
        bookings.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    monthly_revenue = list(
        Payment.objects.filter(
            booking__provider=provider,
            booking__status='Completed',
            status='completed',
        )
        .annotate(month=TruncMonth('paid_at'))
        .values('month')
        .annotate(revenue=Sum('amount'))
        .order_by('month')
    )
    if not monthly_revenue:
        monthly_revenue = list(
            Payment.objects.filter(
                booking__provider=provider,
                booking__status='Completed',
                status='completed',
            )
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(revenue=Sum('amount'))
            .order_by('month')
        )

    response_times = []
    for b in bookings.filter(accepted_at__isnull=False, created_at__isnull=False):
        delta = b.accepted_at - b.created_at
        response_times.append(delta.total_seconds() / 3600)
    avg_response = round(sum(response_times) / len(response_times), 1) if response_times else 0

    return {
        'completion_rate': completion_rate,
        'avg_response_hours': avg_response,
        'monthly_bookings_labels': [r['month'].strftime('%b %Y') if r['month'] else '' for r in monthly_bookings],
        'monthly_bookings_data': [r['count'] for r in monthly_bookings],
        'monthly_revenue_labels': [r['month'].strftime('%b %Y') if r['month'] else '' for r in monthly_revenue],
        'monthly_revenue_data': [float(r['revenue'] or 0) for r in monthly_revenue],
    }


def send_booking_status_email(booking, event_type):
    subject_map = {
        'accepted': 'Your Booking Was Accepted - SMART URS',
        'rejected': 'Booking Update - SMART URS',
        'started': 'Your Service Has Started - SMART URS',
        'completed': 'Service Completed - SMART URS',
    }
    subject = subject_map.get(event_type, 'Booking Update - SMART URS')
    service_name = booking.service.name if booking.service else 'Service'
    html_content = render_to_string('emails/booking_status_update.html', {
        'booking': booking,
        'event_type': event_type,
        'service_name': service_name,
        'provider_name': booking.provider.name if booking.provider else 'Provider',
    })
    email = EmailMultiAlternatives(
        subject=subject,
        body=f'Your booking #{booking.id} status has been updated.',
        to=[booking.user.email],
    )
    email.attach_alternative(html_content, 'text/html')
    try:
        email.send(fail_silently=True)
    except Exception:
        pass
