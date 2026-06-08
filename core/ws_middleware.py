"""WebSocket middleware — reads custom session keys for customer/provider auth."""

import logging
from http.cookies import SimpleCookie

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

logger = logging.getLogger(__name__)


@database_sync_to_async
def _load_session(session_key):
    from django.contrib.sessions.backends.db import SessionStore
    store = SessionStore(session_key=session_key)
    store.load()
    return store


def _parse_session_key(scope):
    """Extract sessionid from WebSocket Cookie header using proper cookie parsing."""
    headers = dict(scope.get('headers', []))
    cookie_header = headers.get(b'cookie', b'').decode('latin-1')
    if not cookie_header:
        return None

    jar = SimpleCookie()
    jar.load(cookie_header)
    morsel = jar.get('sessionid')
    if morsel:
        return morsel.value

    # Fallback: manual parse for edge cases
    for part in cookie_header.split(';'):
        part = part.strip()
        if part.startswith('sessionid='):
            return part.split('=', 1)[1].strip()
    return None


class SessionAuthMiddleware(BaseMiddleware):
    """Attach user_id and provider_id from Django session to the WebSocket scope."""

    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        scope['user_id'] = None
        scope['provider_id'] = None

        session_key = _parse_session_key(scope)
        if session_key:
            try:
                store = await _load_session(session_key)
                scope['user_id'] = store.get('user_id')
                scope['provider_id'] = store.get('provider_id')
                logger.debug(
                    'WS auth: user_id=%s provider_id=%s path=%s',
                    scope['user_id'], scope['provider_id'],
                    scope.get('path', ''),
                )
            except Exception as exc:
                # Session loading failed; user_id and provider_id remain None
                logger.debug('WS session load failed (expected if session expired): %s', type(exc).__name__)

        return await super().__call__(scope, receive, send)
