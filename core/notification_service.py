"""
Central notification service — DB persistence + real-time WebSocket broadcast.
All booking lifecycle events should call helpers here (sync or via Celery).
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Notification


def _broadcast_notification(notification):
    """Push notification payload to the recipient's WebSocket group."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    payload = {
        'type': 'notification',
        'notification': {
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'notification_type': notification.notification_type,
            'booking_id': notification.booking_id,
            'created_at': notification.created_at.strftime('%b %d, %Y %H:%M'),
            'is_read': notification.is_read,
        },
    }

    if notification.user_id:
        group = f'notifications_user_{notification.user_id}'
        async_to_sync(channel_layer.group_send)(group, {
            'type': 'notification_message',
            'payload': payload,
        })
        # Also push updated unread count
        unread = Notification.objects.filter(user_id=notification.user_id, is_read=False).count()
        async_to_sync(channel_layer.group_send)(group, {
            'type': 'notification_message',
            'payload': {'type': 'unread_count', 'count': unread},
        })

    if notification.provider_id:
        group = f'notifications_provider_{notification.provider_id}'
        async_to_sync(channel_layer.group_send)(group, {
            'type': 'notification_message',
            'payload': payload,
        })
        unread = Notification.objects.filter(provider_id=notification.provider_id, is_read=False).count()
        async_to_sync(channel_layer.group_send)(group, {
            'type': 'notification_message',
            'payload': {'type': 'unread_count', 'count': unread},
        })


def create_notification(
    *,
    user=None,
    provider=None,
    booking=None,
    notification_type='booking_created',
    title='',
    message='',
    broadcast=True,
):
    """Persist notification and optionally push via WebSocket."""
    notification = Notification.objects.create(
        user=user,
        provider=provider,
        booking=booking,
        notification_type=notification_type,
        title=title,
        message=message,
    )
    if broadcast:
        _broadcast_notification(notification)
    return notification


# ─── Event-specific helpers ───────────────────────────────────────────────────

def notify_booking_created(booking):
    service_name = booking.service.name if booking.service else 'service'
    create_notification(
        user=booking.user,
        booking=booking,
        notification_type='booking_created',
        title='Booking Created',
        message=f'Your booking #{booking.id} for {service_name} has been created.',
    )


def notify_provider_assigned(booking):
    service_name = booking.service.name if booking.service else 'a service'
    if booking.provider:
        create_notification(
            provider=booking.provider,
            booking=booking,
            notification_type='provider_assigned',
            title='New Booking Assigned',
            message=(
                f'Booking #{booking.id} for {service_name} '
                f'on {booking.booking_date} at {booking.booking_time}. Please accept or reject.'
            ),
        )
    create_notification(
        user=booking.user,
        booking=booking,
        notification_type='provider_assigned',
        title='Provider Assigned',
        message=(
            f'{booking.provider.name if booking.provider else "A provider"} '
            f'has been assigned to your booking #{booking.id}.'
        ),
    )


def notify_booking_accepted(booking):
    create_notification(
        user=booking.user,
        booking=booking,
        notification_type='booking_accepted',
        title='Booking Accepted',
        message=(
            f'Your booking #{booking.id} was accepted by '
            f'{booking.provider.name if booking.provider else "provider"}. You can now chat.'
        ),
    )


def notify_booking_cancelled(booking):
    create_notification(
        user=booking.user,
        booking=booking,
        notification_type='booking_cancelled',
        title='Booking Cancelled',
        message=f'Booking #{booking.id} has been cancelled.',
    )


def notify_service_completed(booking):
    create_notification(
        user=booking.user,
        booking=booking,
        notification_type='service_completed',
        title='Service Completed',
        message=f'Your booking #{booking.id} has been completed. Please leave a review!',
    )


def notify_review_received(booking, rating):
    if booking.provider:
        create_notification(
            provider=booking.provider,
            booking=booking,
            notification_type='review_received',
            title='New Review Received',
            message=f'You received a {rating}-star review for booking #{booking.id}.',
        )


def notify_new_chat_message(booking_id, msg_data, sender_role):
    from .models import Booking
    try:
        booking = Booking.objects.select_related('user', 'provider').get(id=booking_id)
    except Booking.DoesNotExist:
        return

    preview = msg_data.get('content', '')[:80]
    if sender_role == 'customer' and booking.provider:
        create_notification(
            provider=booking.provider,
            booking=booking,
            notification_type='new_message',
            title='New Chat Message',
            message=f'{booking.user.name}: {preview}',
        )
    elif sender_role == 'provider' and booking.user:
        create_notification(
            user=booking.user,
            booking=booking,
            notification_type='new_message',
            title='New Chat Message',
            message=f'{booking.provider.name}: {preview}',
        )
