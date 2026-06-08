"""Marketplace helpers: notifications and provider time slots."""

from datetime import time

from .models import ProviderTimeSlot, Booking, ServiceProvider
from .notification_service import (
    notify_provider_assigned as notify_provider_new_booking,
    notify_booking_accepted as notify_customer_booking_accepted,
)

# Default working hours: 9 AM – 5 PM
DEFAULT_SLOT_HOURS = list(range(9, 18))


def is_slot_available(provider, booking_date, booking_time):
    """Check if a provider is free at the given date/time."""
    slot = ProviderTimeSlot.objects.filter(
        provider=provider, date=booking_date, time=booking_time,
    ).first()
    if slot and slot.status in ('occupied', 'unavailable'):
        return False
    return not Booking.objects.filter(
        provider=provider,
        booking_date=booking_date,
        booking_time=booking_time,
    ).exclude(status='Cancelled').exists()


def get_available_slots(service, booking_date):
    """Return list of available time slots for a service on a given date."""
    providers = ServiceProvider.objects.filter(
        service_type=service.service_type, availability=True,
    ).order_by('-rating', '-experience_years')

    available = []
    for hour in DEFAULT_SLOT_HOURS:
        t = time(hour, 0)
        free_providers = [p for p in providers if is_slot_available(p, booking_date, t)]
        if free_providers:
            available.append({
                'time': t.strftime('%H:%M'),
                'label': t.strftime('%I:%M %p'),
                'count': len(free_providers),
            })
    return available


def assign_provider_for_slot(service, booking_date, booking_time, preferred_provider=None):
    """Assign best available provider; tries preferred first, then falls back."""
    providers = ServiceProvider.objects.filter(
        service_type=service.service_type, availability=True,
    ).order_by('-rating', '-experience_years')

    if preferred_provider and is_slot_available(preferred_provider, booking_date, booking_time):
        return preferred_provider

    for provider in providers:
        if is_slot_available(provider, booking_date, booking_time):
            return provider
    return None


def mark_slot_occupied(provider, booking_date, booking_time):
    """Mark a slot as occupied after booking."""
    ProviderTimeSlot.objects.update_or_create(
        provider=provider,
        date=booking_date,
        time=booking_time,
        defaults={'status': 'occupied'},
    )
