"""
ASGI config for SMART URS — HTTP + WebSocket via Django Channels.
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OnDemand_HomeServices.settings')

django_asgi_app = get_asgi_application()

from core.routing import websocket_urlpatterns  # noqa: E402
from core.ws_middleware import SessionAuthMiddleware  # noqa: E402

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        SessionAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
