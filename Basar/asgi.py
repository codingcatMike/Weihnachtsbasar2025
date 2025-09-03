import os

# 1️⃣ SETTINGS zuerst setzen
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Basar.settings")

# 2️⃣ Django initialisieren
from django.core.asgi import get_asgi_application
django_application = get_asgi_application()

# 3️⃣ Channels imports **nach** Django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# 4️⃣ main.routing import **erst jetzt**
import main.routing

# 5️⃣ Channels ASGI application
application = ProtocolTypeRouter({
    "http": django_application,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            main.routing.websocket_urlpatterns
        )
    ),
})

