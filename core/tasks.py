"""
Celery background tasks for SMART URS.
Emails, notifications, and reminders run here so HTTP requests return instantly.
"""

from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_confirmation_email(self, booking_id):
    """Send booking confirmation email to customer."""
    from .models import Booking
    try:
        booking = Booking.objects.select_related('user', 'service', 'provider').get(id=booking_id)
    except Booking.DoesNotExist:
        return

    service_name = booking.service.name if booking.service else 'Service'
    html_content = render_to_string('emails/booking_confirmation.html', {
        'user_name': booking.user.name,
        'service_name': service_name,
        'provider_name': booking.provider.name if booking.provider else 'Will be Assigned Soon',
        'booking_date': booking.booking_date,
        'booking_time': booking.booking_time,
        'booking_id': booking.id,
    })
    email = EmailMultiAlternatives(
        subject='Booking Confirmed - SMART URS',
        body='Your booking has been confirmed.',
        to=[booking.user.email],
    )
    email.attach_alternative(html_content, 'text/html')
    try:
        email.send(fail_silently=False)
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_status_email_task(self, booking_id, event_type):
    """Send status update email (accepted, rejected, started, completed)."""
    from .models import Booking
    from .provider_utils import send_booking_status_email
    try:
        booking = Booking.objects.select_related('user', 'service', 'provider').get(id=booking_id)
    except Booking.DoesNotExist:
        return
    try:
        send_booking_status_email(booking, event_type)
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_provider_assigned_email_task(self, booking_id):
    """Email customer when admin assigns a provider."""
    from .models import Booking
    try:
        booking = Booking.objects.select_related('user', 'service', 'provider').get(id=booking_id)
    except Booking.DoesNotExist:
        return
    if not booking.provider:
        return
    html_content = render_to_string('emails/provider_assigned.html', {
        'user_name': booking.user.name,
        'provider_name': booking.provider.name,
        'provider_phone': booking.provider.phone,
        'provider_rating': booking.provider.rating,
        'service_name': booking.service.name if booking.service else 'Service',
    })
    email = EmailMultiAlternatives(
        subject='Provider Assigned - SMART URS',
        body='A provider has been assigned to your booking.',
        to=[booking.user.email],
    )
    email.attach_alternative(html_content, 'text/html')
    try:
        email.send(fail_silently=False)
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def dispatch_notification_task(
    notification_type, booking_id=None,
    user_id=None, provider_id=None,
    title='', message='', rating=None,
):
    """
    Create a notification in the background and broadcast via WebSocket.
    Maps notification_type to the correct service helper.
    """
    from .models import Booking, User, ServiceProvider
    from . import notification_service as ns

    booking = None
    if booking_id:
        booking = Booking.objects.select_related('user', 'service', 'provider').filter(id=booking_id).first()

    dispatch_map = {
        'booking_created': lambda: ns.notify_booking_created(booking),
        'provider_assigned': lambda: ns.notify_provider_assigned(booking),
        'booking_accepted': lambda: ns.notify_booking_accepted(booking),
        'booking_cancelled': lambda: ns.notify_booking_cancelled(booking),
        'service_completed': lambda: ns.notify_service_completed(booking),
        'review_received': lambda: ns.notify_review_received(booking, rating),
    }

    handler = dispatch_map.get(notification_type)
    if handler and booking:
        handler()
    elif title and (user_id or provider_id):
        user = User.objects.filter(id=user_id).first() if user_id else None
        provider = ServiceProvider.objects.filter(id=provider_id).first() if provider_id else None
        ns.create_notification(
            user=user,
            provider=provider,
            booking=booking,
            notification_type=notification_type,
            title=title,
            message=message,
        )


@shared_task
def send_service_reminder_task(booking_id):
    """Remind customer and provider 24h before scheduled service."""
    from .models import Booking
    from .notification_service import create_notification
    try:
        booking = Booking.objects.select_related('user', 'provider', 'service').get(id=booking_id)
    except Booking.DoesNotExist:
        return
    if booking.status in ('Cancelled', 'Completed'):
        return
    service_name = booking.service.name if booking.service else 'service'
    create_notification(
        user=booking.user,
        booking=booking,
        notification_type='service_reminder',
        title='Service Reminder',
        message=f'Reminder: {service_name} is scheduled for {booking.booking_date} at {booking.booking_time}.',
    )
    if booking.provider:
        create_notification(
            provider=booking.provider,
            booking=booking,
            notification_type='service_reminder',
            title='Service Reminder',
            message=f'Reminder: Booking #{booking.id} is tomorrow at {booking.booking_time}.',
        )


@shared_task
def send_review_reminder_task(booking_id):
    """Remind customer to leave a review after service completion."""
    from .models import Booking, Review
    from .notification_service import create_notification
    try:
        booking = Booking.objects.select_related('user', 'service').get(id=booking_id)
    except Booking.DoesNotExist:
        return
    if booking.status != 'Completed':
        return
    if Review.objects.filter(booking=booking).exists():
        return
    service_name = booking.service.name if booking.service else 'service'
    create_notification(
        user=booking.user,
        booking=booking,
        notification_type='review_reminder',
        title='Leave a Review',
        message=f'How was your {service_name}? Please leave a review for booking #{booking.id}.',
    )


@shared_task
def schedule_booking_reminders(booking_id):
    """Schedule service reminder (24h before) and review reminder (2h after completion)."""
    from .models import Booking
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return
    if booking.booking_date:
        from datetime import datetime
        from django.utils import timezone as tz
        service_dt = tz.make_aware(
            datetime.combine(booking.booking_date, booking.booking_time or datetime.min.time())
        )
        reminder_eta = service_dt - timedelta(hours=24)
        if reminder_eta > tz.now():
            send_service_reminder_task.apply_async(args=[booking_id], eta=reminder_eta)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_payment_receipt_email(self, payment_id):
    """Send payment receipt after successful Razorpay verification."""
    from .models import Payment
    try:
        payment = Payment.objects.select_related('booking__user', 'booking__service').get(id=payment_id)
    except Payment.DoesNotExist:
        return
    booking = payment.booking
    html_content = render_to_string('emails/payment_receipt.html', {
        'payment': payment,
        'booking': booking,
        'user_name': booking.user.name,
        'service_name': payment.service_name,
    })
    email = EmailMultiAlternatives(
        subject=f'Payment Receipt — SMART URS #{payment.transaction_id or payment.id}',
        body='Your payment was successful.',
        to=[booking.user.email],
    )
    email.attach_alternative(html_content, 'text/html')
    try:
        email.send(fail_silently=False)
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_invoice_email_task(self, invoice_id):
    """Email invoice PDF to customer after service completion."""
    from .models import Invoice
    try:
        invoice = Invoice.objects.select_related('booking__user', 'booking__service').get(id=invoice_id)
    except Invoice.DoesNotExist:
        return
    booking = invoice.booking
    html_content = render_to_string('emails/invoice_ready.html', {
        'invoice': invoice,
        'booking': booking,
        'user_name': booking.user.name,
    })
    email = EmailMultiAlternatives(
        subject=f'Invoice {invoice.invoice_number} — SMART URS',
        body='Your service invoice is attached.',
        to=[booking.user.email],
    )
    email.attach_alternative(html_content, 'text/html')
    if invoice.pdf_file:
        email.attach(invoice.invoice_number + '.pdf', invoice.pdf_file.read(), 'application/pdf')
    try:
        email.send(fail_silently=False)
    except Exception as exc:
        raise self.retry(exc=exc)
