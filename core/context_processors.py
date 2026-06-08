from django.conf import settings
from django.utils import timezone

from .models import Notification
from .chat_utils import (
    get_unread_message_count_for_user,
    get_unread_message_count_for_provider,
)


def add_today_variable(request):
    return {'today': timezone.now().date()}


def razorpay_settings(request):
    return {
        'RAZORPAY_KEY_ID': getattr(settings, 'RAZORPAY_KEY_ID', ''),
    }


def notification_counts(request):
    """Unread notification + chat counts for navbar badges."""
    unread_user = 0
    unread_provider = 0
    unread_chat_user = 0
    unread_chat_provider = 0
    user_id = request.session.get('user_id')
    provider_id = request.session.get('provider_id')
    if user_id:
        unread_user = Notification.objects.filter(user_id=user_id, is_read=False).count()
        unread_chat_user = get_unread_message_count_for_user(user_id)
    if provider_id:
        unread_provider = Notification.objects.filter(provider_id=provider_id, is_read=False).count()
        unread_chat_provider = get_unread_message_count_for_provider(provider_id)
    return {
        'unread_notifications': unread_user,
        'unread_provider_notifications': unread_provider,
        'unread_chat_messages': unread_chat_user,
        'unread_provider_chat_messages': unread_chat_provider,
    }
