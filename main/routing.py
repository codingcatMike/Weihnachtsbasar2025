from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/pay/$", consumers.PayConsumer.as_asgi()),
    re_path(r"ws/pay_screen/$", consumers.PayScreenConsumer.as_asgi()),
]
