"""Chat room helpers — access control and room lifecycle."""

from .models import ChatRoom, Booking

# Chat opens once a provider accepts the booking
CHAT_ALLOWED_STATUSES = ('Accepted', 'In Progress', 'Completed')


def can_access_chat(booking, user_id=None, provider_id=None):
    """
    Return (allowed: bool, role: str|None).
    Only the booking's customer or assigned provider may chat.
    """
    if booking.status not in CHAT_ALLOWED_STATUSES:
        return False, None
    if user_id and booking.user_id == user_id:
        return True, 'customer'
    if provider_id and booking.provider_id == provider_id:
        return True, 'provider'
    return False, None


def ensure_chat_room(booking):
    """Create a chat room when a booking is accepted."""
    if booking.status in CHAT_ALLOWED_STATUSES:
        ChatRoom.objects.get_or_create(booking=booking)
        return True
    return False


def get_unread_message_count_for_user(user_id):
    from .models import ChatMessage
    return ChatMessage.objects.filter(
        room__booking__user_id=user_id,
        sender_type='provider',
        is_read=False,
    ).count()


def get_unread_message_count_for_provider(provider_id):
    from .models import ChatMessage
    return ChatMessage.objects.filter(
        room__booking__provider_id=provider_id,
        sender_type='customer',
        is_read=False,
    ).count()
