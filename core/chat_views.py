"""HTTP views for booking-scoped chat rooms."""

import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_GET, require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Booking, ChatMessage, ChatRoom
from .chat_utils import can_access_chat
from .chat_api import get_chat_auth, save_and_broadcast_message, serialize_message
from .provider_utils import get_provider_from_session, provider_session_required
from .views import get_custom_user_from_request


def _get_chat_context(booking, role, user_name):
    return {
        'booking': booking,
        'role': role,
        'user_name': user_name,
        'other_party': (
            booking.provider.name if role == 'customer'
            else booking.user.name
        ),
        'service_name': booking.service.name if booking.service else 'Service',
    }


@ensure_csrf_cookie
def booking_chat(request, booking_id):
    """Customer chat view — only for accepted+ bookings."""
    user = get_custom_user_from_request(request)
    if not user:
        return redirect('login')

    booking = get_object_or_404(
        Booking.objects.select_related('provider', 'service', 'user'),
        id=booking_id,
    )
    allowed, role = can_access_chat(booking, user_id=user.id)
    if not allowed:
        messages.error(request, 'Chat is available only after your booking is accepted.')
        return redirect('my_bookings')

    # Mark provider messages as read when customer opens chat
    ChatMessage.objects.filter(
        room__booking=booking, sender_type='provider', is_read=False,
    ).update(is_read=True)

    return render(request, 'chat/room.html', _get_chat_context(booking, role, user.name))


@ensure_csrf_cookie
@provider_session_required
def provider_booking_chat(request, booking_id):
    """Provider chat view — session auth only (availability must not block chat)."""
    provider = get_provider_from_session(request)
    booking = get_object_or_404(
        Booking.objects.select_related('provider', 'service', 'user'),
        id=booking_id,
        provider=provider,
    )
    allowed, role = can_access_chat(booking, provider_id=provider.id)
    if not allowed:
        messages.error(request, 'Chat opens once you accept the booking.')
        return redirect('provider_dashboard')

    ChatMessage.objects.filter(
        room__booking=booking, sender_type='customer', is_read=False,
    ).update(is_read=True)

    return render(request, 'chat/room.html', _get_chat_context(booking, role, provider.name))


@require_POST
def mark_chat_read(request, booking_id):
    """Mark incoming messages as read when user opens chat."""
    user = get_custom_user_from_request(request)
    provider = get_provider_from_session(request)

    booking = get_object_or_404(Booking, id=booking_id)
    allowed, role = can_access_chat(
        booking,
        user_id=user.id if user else None,
        provider_id=provider.id if provider else None,
    )
    if not allowed:
        return redirect('home')

    if role == 'customer':
        ChatMessage.objects.filter(
            room__booking=booking, sender_type='provider', is_read=False,
        ).update(is_read=True)
        return redirect('booking_chat', booking_id=booking_id)
    elif role == 'provider':
        ChatMessage.objects.filter(
            room__booking=booking, sender_type='customer', is_read=False,
        ).update(is_read=True)
        return redirect('provider_booking_chat', booking_id=booking_id)
    return redirect('home')


@require_GET
def chat_messages_api(request, booking_id):
    """Poll messages (HTTP fallback when WebSocket unavailable)."""
    booking, role, _ = get_chat_auth(request, booking_id)
    if not booking:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    since_id = request.GET.get('since', 0)
    try:
        since_id = int(since_id)
    except (TypeError, ValueError):
        since_id = 0

    try:
        room = ChatRoom.objects.get(booking=booking)
        qs = room.messages.select_related('sender_user', 'sender_provider').order_by('created_at')
        if since_id:
            qs = qs.filter(id__gt=since_id)
        messages_data = [serialize_message(m) for m in qs]
    except ChatRoom.DoesNotExist:
        messages_data = []

    return JsonResponse({'messages': messages_data, 'role': role})


@require_POST
def chat_send_api(request, booking_id):
    """
    Send message via HTTP — works even when WebSocket server is not running.
    Also broadcasts to WebSocket clients when channel layer is available.
    """
    booking, role, actor = get_chat_auth(request, booking_id)
    if not booking:
        return JsonResponse({'error': 'Unauthorized or chat not available'}, status=403)

    try:
        body = json.loads(request.body.decode('utf-8'))
        content = (body.get('message') or '').strip()
    except (json.JSONDecodeError, UnicodeDecodeError):
        content = (request.POST.get('message') or '').strip()

    if not content:
        return JsonResponse({'error': 'Message cannot be empty'}, status=400)

    user_id = actor.id if role == 'customer' else None
    provider_id = actor.id if role == 'provider' else None
    msg_data = save_and_broadcast_message(
        booking, role,
        user_id=user_id,
        provider_id=provider_id,
        content=content,
    )
    return JsonResponse({'success': True, 'message': msg_data})
