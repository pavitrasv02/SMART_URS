"""WebSocket consumers for real-time chat and notifications."""

import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Booking, ChatRoom, ChatMessage, Notification
from .chat_utils import can_access_chat
from .chat_api import (
    serialize_message,
    persist_chat_message,
    room_group_name,
    broadcast_chat_message,
)

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope.get('user_id')
        self.provider_id = self.scope.get('provider_id')
        if self.user_id:
            self.group_name = f'notifications_user_{self.user_id}'
        elif self.provider_id:
            self.group_name = f'notifications_provider_{self.provider_id}'
        else:
            await self.close(code=4001)
            return
        try:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
        except Exception as exc:
            logger.warning('Notification group_add failed: %s', exc)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            try:
                await self.channel_layer.group_discard(self.group_name, self.channel_name)
            except Exception:
                pass

    async def notification_message(self, event):
        await self.send(text_data=json.dumps(event['payload']))


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Real-time chat consumer.
    Room: chat_booking_{booking_id} — both customer and provider join the same group.
    """

    async def connect(self):
        self.booking_id = int(self.scope['url_route']['kwargs']['booking_id'])
        self.user_id = self.scope.get('user_id')
        self.provider_id = self.scope.get('provider_id')
        self.room_group = room_group_name(self.booking_id)

        allowed, role = await self._check_access()
        if not allowed:
            logger.warning(
                'Chat WS rejected booking=%s user_id=%s provider_id=%s',
                self.booking_id, self.user_id, self.provider_id,
            )
            await self.close(code=4003)
            return

        self.role = role
        try:
            await self.channel_layer.group_add(self.room_group, self.channel_name)
        except Exception as exc:
            logger.warning('Chat group_add failed (poll fallback active): %s', exc)

        await self.accept()
        logger.info(
            'Chat WS connected booking=%s role=%s group=%s channel=%s',
            self.booking_id, role, self.room_group, self.channel_name,
        )

        history = await self._get_history()
        await self.send(text_data=json.dumps({'type': 'history', 'messages': history}))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group'):
            try:
                await self.channel_layer.group_discard(self.room_group, self.channel_name)
            except Exception:
                pass
        logger.info('Chat WS disconnected booking=%s code=%s', self.booking_id, close_code)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'type': 'error', 'message': 'Invalid JSON'}))
            return

        content = (data.get('message') or '').strip()
        if not content:
            return

        msg_data = await self._save_message(content)
        if not msg_data:
            await self.send(text_data=json.dumps({'type': 'error', 'message': 'Save failed'}))
            return

        # Broadcast to BOTH customer and provider in the same room
        try:
            await self.channel_layer.group_send(self.room_group, {
                'type': 'chat_message',
                'payload': msg_data,
            })
            logger.info('group_send OK room=%s msg_id=%s', self.room_group, msg_data['id'])
        except Exception as exc:
            logger.error('group_send FAILED room=%s: %s', self.room_group, exc)
            await self.send(text_data=json.dumps({'type': 'message', 'message': msg_data}))

    async def chat_message(self, event):
        """Handler for channel layer group_send — delivers to all room members."""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['payload'],
        }))

    @database_sync_to_async
    def _check_access(self):
        try:
            booking = Booking.objects.select_related('user', 'provider').get(id=self.booking_id)
        except Booking.DoesNotExist:
            return False, None
        return can_access_chat(booking, self.user_id, self.provider_id)

    @database_sync_to_async
    def _get_history(self):
        try:
            room = ChatRoom.objects.get(booking_id=self.booking_id)
        except ChatRoom.DoesNotExist:
            return []
        qs = room.messages.select_related('sender_user', 'sender_provider').order_by('created_at')
        return [serialize_message(m) for m in qs]

    @database_sync_to_async
    def _save_message(self, content):
        try:
            booking = Booking.objects.get(id=self.booking_id)
        except Booking.DoesNotExist:
            return None
        user_id = self.user_id if self.role == 'customer' else None
        provider_id = self.provider_id if self.role == 'provider' else None
        msg = persist_chat_message(
            booking, self.role, user_id=user_id, provider_id=provider_id, content=content,
        )
        data = serialize_message(msg)
        try:
            from .notification_service import notify_new_chat_message
            notify_new_chat_message(self.booking_id, data, sender_role=self.role)
        except Exception:
            pass
        return data
