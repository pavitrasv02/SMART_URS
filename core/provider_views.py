"""Provider Management System views for SMART URS."""

import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Count

from .models import ServiceProvider, Booking, ProviderTimeSlot, Notification
from .provider_utils import (
    get_provider_from_request,
    provider_login_required,
    get_provider_bookings,
    get_provider_earnings,
    get_provider_rating_stats,
    get_provider_analytics,
)
from .chat_utils import ensure_chat_room, CHAT_ALLOWED_STATUSES
from .tasks import (
    send_booking_status_email_task,
    dispatch_notification_task,
    send_review_reminder_task,
)


def _get_provider_booking_or_403(request, booking_id):
    provider = get_provider_from_request(request)
    booking = get_object_or_404(
        Booking.objects.select_related('user', 'service'),
        id=booking_id,
        provider=provider,
    )
    return provider, booking


def provider_login(request):
    if get_provider_from_request(request):
        return redirect('provider_dashboard')
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        provider = ServiceProvider.objects.filter(
            email=email, password=password, availability=True
        ).first()
        if provider:
            request.session['provider_id'] = provider.id
            messages.success(request, f'Welcome back, {provider.name}!')
            return redirect('provider_dashboard')
        messages.error(request, 'Invalid credentials or account deactivated.')
    return render(request, 'provider/login.html')


def provider_logout(request):
    request.session.pop('provider_id', None)
    messages.info(request, 'You have been logged out.')
    return redirect('provider_login')


@provider_login_required
def provider_dashboard(request):
    provider = get_provider_from_request(request)
    bookings = get_provider_bookings(provider)
    earnings = get_provider_earnings(provider)
    ratings = get_provider_rating_stats(provider)
    analytics = get_provider_analytics(provider)

    context = {
        'provider': provider,
        'total_assigned': bookings.count(),
        'pending_count': bookings.filter(status='Provider Assigned').count(),
        'in_progress_count': bookings.filter(status='In Progress').count(),
        'completed_count': bookings.filter(status='Completed').count(),
        'accepted_count': bookings.filter(status='Accepted').count(),
        'average_rating': ratings['average'],
        'earnings': earnings,
        'ratings': ratings,
        'star_breakdown': [(s, ratings['stars'][s]) for s in range(5, 0, -1)],
        'recent_bookings': bookings.order_by('-id')[:10],
        'assigned_bookings': bookings.exclude(
            status__in=['Completed', 'Cancelled']
        ).order_by('-id'),
        'chat_enabled_statuses': CHAT_ALLOWED_STATUSES,
        'completion_rate': analytics['completion_rate'],
        'avg_response_hours': analytics['avg_response_hours'],
        'chart_bookings_labels': json.dumps(analytics['monthly_bookings_labels']),
        'chart_bookings_data': json.dumps(analytics['monthly_bookings_data']),
        'chart_revenue_labels': json.dumps(analytics['monthly_revenue_labels']),
        'chart_revenue_data': json.dumps(analytics['monthly_revenue_data']),
    }
    return render(request, 'provider/dashboard.html', context)


@provider_login_required
def provider_profile(request):
    provider = get_provider_from_request(request)
    if request.method == 'POST':
        action = request.POST.get('action', 'profile')
        if action == 'add_slot':
            from datetime import datetime
            slot_date = request.POST.get('slot_date')
            slot_time = request.POST.get('slot_time')
            slot_status = request.POST.get('slot_status', 'unavailable')
            if slot_date and slot_time:
                ProviderTimeSlot.objects.update_or_create(
                    provider=provider,
                    date=datetime.strptime(slot_date, '%Y-%m-%d').date(),
                    time=datetime.strptime(slot_time, '%H:%M').time(),
                    defaults={'status': slot_status},
                )
                messages.success(request, 'Time slot updated.')
            return redirect('provider_profile')
        provider.name = request.POST.get('name', provider.name)
        provider.phone = request.POST.get('phone', provider.phone)
        provider.description = request.POST.get('description', provider.description)
        provider.experience_years = int(request.POST.get('experience_years') or provider.experience_years)
        provider.languages = request.POST.get('languages', provider.languages)
        provider.working_hours = request.POST.get('working_hours', provider.working_hours)
        provider.availability = request.POST.get('availability') == 'on'
        provider.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('provider_profile')
    time_slots = ProviderTimeSlot.objects.filter(provider=provider).order_by('date', 'time')[:20]
    return render(request, 'provider/profile.html', {
        'provider': provider,
        'time_slots': time_slots,
    })


@provider_login_required
def provider_notifications(request):
    provider = get_provider_from_request(request)
    notifications = Notification.objects.filter(provider=provider).select_related('booking')
    return render(request, 'provider/notifications.html', {'notifications': notifications})


@provider_login_required
@require_POST
def provider_mark_notification_read(request, notification_id):
    provider = get_provider_from_request(request)
    Notification.objects.filter(id=notification_id, provider=provider).update(is_read=True)
    return redirect('provider_notifications')


@provider_login_required
@require_POST
def accept_booking(request, booking_id):
    provider, booking = _get_provider_booking_or_403(request, booking_id)
    if booking.status != 'Provider Assigned':
        messages.error(request, 'This booking cannot be accepted in its current state.')
        return redirect('provider_dashboard')
    booking.status = 'Accepted'
    booking.accepted_at = timezone.now()
    booking.save()

    ensure_chat_room(booking)

    # Background email + notification
    send_booking_status_email_task.delay(booking.id, 'accepted')
    dispatch_notification_task.delay('booking_accepted', booking_id=booking.id)

    messages.success(request, f'Booking #{booking.id} accepted. Chat is now open.')
    return redirect('provider_dashboard')


@provider_login_required
@require_POST
def reject_booking(request, booking_id):
    provider, booking = _get_provider_booking_or_403(request, booking_id)
    if booking.status not in ('Provider Assigned', 'Accepted'):
        messages.error(request, 'This booking cannot be rejected in its current state.')
        return redirect('provider_dashboard')
    booking.status = 'Cancelled'
    booking.cancelled_at = timezone.now()
    booking.save()

    send_booking_status_email_task.delay(booking.id, 'rejected')
    dispatch_notification_task.delay('booking_cancelled', booking_id=booking.id)

    messages.warning(request, f'Booking #{booking.id} rejected.')
    return redirect('provider_dashboard')


@provider_login_required
@require_POST
def start_service(request, booking_id):
    provider, booking = _get_provider_booking_or_403(request, booking_id)
    if booking.status != 'Accepted':
        messages.error(request, 'Only accepted bookings can be started.')
        return redirect('provider_dashboard')
    booking.status = 'In Progress'
    booking.started_at = timezone.now()
    booking.save()

    send_booking_status_email_task.delay(booking.id, 'started')
    messages.success(request, f'Service started for booking #{booking.id}.')
    return redirect('provider_dashboard')


@provider_login_required
@require_POST
def complete_service(request, booking_id):
    provider, booking = _get_provider_booking_or_403(request, booking_id)
    if booking.status != 'In Progress':
        messages.error(request, 'Only in-progress bookings can be completed.')
        return redirect('provider_dashboard')
    booking.status = 'Completed'
    booking.completed_at = timezone.now()
    booking.save()

    send_booking_status_email_task.delay(booking.id, 'completed')
    dispatch_notification_task.delay('service_completed', booking_id=booking.id)
    send_review_reminder_task.apply_async(args=[booking.id], countdown=7200)

    from .payment_utils import create_invoice_for_booking
    from .tasks import send_invoice_email_task
    invoice = create_invoice_for_booking(booking)
    send_invoice_email_task.delay(invoice.id)

    messages.success(request, f'Booking #{booking.id} marked as completed.')
    return redirect('provider_dashboard')
