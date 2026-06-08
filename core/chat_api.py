"""HTTP + WebSocket broadcast helpers for chat."""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from .models import ChatRoom, ChatMessage

logger = logging.getLogger(__name__)

ROOM_PREFIX = 'chat_booking_'


def room_group_name(booking_id):
    """Single canonical room name used by consumers and broadcast."""
    return f'{ROOM_PREFIX}{booking_id}'


def serialize_message(msg):
    sender_name = 'Unknown'
    if msg.sender_type == 'customer' and msg.sender_user:
        sender_name = msg.sender_user.name
    elif msg.sender_type == 'provider' and msg.sender_provider:
        sender_name = msg.sender_provider.name
    return {
        'id': msg.id,
        'sender_type': msg.sender_type,
        'sender_name': sender_name,
        'content': msg.content,
        'created_at': timezone.localtime(msg.created_at).strftime('%b %d, %Y %I:%M %p'),
        'is_read': msg.is_read,
    }


def persist_chat_message(booking, role, user_id=None, provider_id=None, content=''):
    """Save message to DB only (no broadcast)."""
    room, _ = ChatRoom.objects.get_or_create(booking=booking)
    if role == 'customer':
        msg = ChatMessage.objects.create(
            room=room,
            sender_type='customer',
            sender_user_id=user_id,
            content=content,
        )
    else:
        msg = ChatMessage.objects.create(
            room=room,
            sender_type='provider',
            sender_provider_id=provider_id,
            content=content,
        )
    return ChatMessage.objects.select_related('sender_user', 'sender_provider').get(id=msg.id)


def broadcast_chat_message(booking_id, msg_data):
    """Push message to all WebSocket clients in the booking room via group_send."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning('No channel layer — WS broadcast skipped booking=%s', booking_id)
        return False
    try:
        async_to_sync(channel_layer.group_send)(
            room_group_name(booking_id),
            {'type': 'chat_message', 'payload': msg_data},
        )
        logger.info('Broadcast to %s msg_id=%s', room_group_name(booking_id), msg_data.get('id'))
        return True
    except Exception as exc:
        logger.error('Chat broadcast failed booking=%s: %s', booking_id, exc)
        return False


def save_and_broadcast_message(booking, role, user_id=None, provider_id=None, content=''):
    """Persist message, broadcast to room, notify recipient."""
    msg = persist_chat_message(booking, role, user_id, provider_id, content)
    data = serialize_message(msg)
    broadcast_chat_message(booking.id, data)

    try:
        from .notification_service import notify_new_chat_message
        notify_new_chat_message(booking.id, data, sender_role=role)
    except Exception as exc:
        logger.warning('Chat notification failed (message saved): %s', exc)
    return data


def get_chat_auth(request, booking_id):
    """Return (booking, role, actor) or (None, None, None)."""
    from .views import get_custom_user_from_request
    from .provider_utils import get_provider_from_session
    from .models import Booking
    from .chat_utils import can_access_chat

    user = get_custom_user_from_request(request)
    provider = get_provider_from_session(request)
    try:
        booking = Booking.objects.select_related('user', 'provider', 'service').get(id=booking_id)
    except Booking.DoesNotExist:
        return None, None, None

    allowed, role = can_access_chat(
        booking,
        user_id=user.id if user else None,
        provider_id=provider.id if provider else None,
    )
    if not allowed:
        return None, None, None
    return booking, role, user if role == 'customer' else provider
