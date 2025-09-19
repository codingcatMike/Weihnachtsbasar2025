# main/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Order, Income
from django.conf import settings
from django.urls import reverse
import io
import base64
import qrcode
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async

class CustomerConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.cid = None

    async def disconnect(self, close_code):
        if self.cid:
            await self.channel_layer.group_discard(f"customer_{self.cid}", self.channel_name)

    async def receive_json(self, content):
        if "cid" in content:
            self.cid = content["cid"]
            self.group_name = f"customer_{self.cid}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)

    async def order_update(self, event):
        await self.send_json(event["order"])


class PayConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "pay_updates"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        # In PayConsumer.connect
        print(f"WebSocket connected, adding to group {self.group_name}")


        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message", "")

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "pay_message",
                "message": message
            }
        )

    async def pay_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"]
        }))

    async def new_order(self, event):
        await self.send(text_data=json.dumps({
            "orders": event["orders"],
            "income": event.get("income_money", 0),
        }))



class PayScreenConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "pay_screen_updates"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Hilfsfunktion: QR-Code als Base64 erzeugen
    def generate_order_qr_base64(self, order_id):
        print("Generating QR code for order:", order_id)
        url = settings.SITE_URL + reverse("receipt_pdf", args=[order_id])
        qr = qrcode.make(url)
        buf = io.BytesIO()
        qr.save(buf, format="PNG")
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode("utf-8")
        return f"data:image/png;base64,{img_str}"

    # Hilfsfunktion: Order live senden
    def send_onscreen_order(self, order_id):
        channel_layer = get_channel_layer()
        order = Order.objects.get(id=order_id)

        items = [
            {
                "name": item.product.name,
                "quantity": item.quantity,
                "price": float(item.product.price)
            }
            for item in order.orderitem_set.all()
        ]

        order_data = {
            "id": order.id,
            "customer_id": order.customer.id,
            "price": float(order.price),
            "items": items,
            "qr_code": self.generate_order_qr_base64(order.id),
        }

        # An alle im Channel senden
        async_to_sync(channel_layer.group_send)(
            self.group_name,
            {
                "type": "new_onscreen",
                "order": order_data,
            }
        )

    # Event-Handler für Clients
    async def new_onscreen(self, event):
        await self.send(text_data=json.dumps({
            "order": event["order"]
        }))
    async def order_paid(self, event):
        # Send a message to client to clear the order
        await self.send(text_data=json.dumps({
            "order": None,  # frontend interprets this as "clear"
            "paid_order_id": event["order_id"]  # optional
        }))

class CustomerConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.cid = None

    async def disconnect(self, close_code):
        if self.cid:
            await self.channel_layer.group_discard(f"customer_{self.cid}", self.channel_name)

    async def receive_json(self, content):
        if "cid" in content:
            self.cid = content["cid"]
            self.group_name = f"customer_{self.cid}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)

    async def order_update(self, event):
        await self.send_json(event["order"])

from asgiref.sync import sync_to_async

from channels.generic.websocket import AsyncWebsocketConsumer
import json

class KitchenConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("kitchen", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("kitchen", self.channel_name)

    # Handler for messages sent with "type": "kitchen_update"
    async def kitchen_update(self, event):
        # event["data"] is what you sent from announce_order_update
        await self.send(text_data=json.dumps(event["data"]))


# main/utils.py
def send_orders_update():
    print("Sending orders update to WebSocket clients...")
    channel_layer = get_channel_layer()
    orders = Order.objects.filter(payed=False)
    print(f"Found {orders.count()} unpaid orders.")
    incomes = Income.objects.all()
    income_money = sum(income.price for income in incomes)
    orders_data = []
    for order in orders:
        items = [
            {"name": item.product.name, "quantity": item.quantity}
            for item in order.orderitem_set.all()
        ]
        orders_data.append({
            "id": order.id,
            "customer_id": order.customer.id,
            "price": order.price,
            "items": items
        })

    async_to_sync(channel_layer.group_send)(
        "pay_updates",
        {
            "type": "new_order",
            "orders": orders_data,
            "income_money": income_money
        }
    )


def get_new_onscreen_order(id):
    channel_layer = get_channel_layer()
    order = Order.objects.get(id=id)
    items = [
            {"name": item.product.name, "quantity": item.quantity}
            for item in order.orderitem_set.all()
        ]
    order_data = ({
        "id": order.id,
        "customer_id": order.customer.id,
        "price": order.price,
        "items": items,
        
    })

    async_to_sync(channel_layer.group_send)(
        "pay_updates",
        {
            "type": "new_onscreen",
            "order": order_data,
        }
    )



def send_order_customer_update(order):
    channel_layer = get_channel_layer()

    # Use the correct related manager
    items = [
        {"name": item.product.name, "quantity": item.quantity}
        for item in order.orderitem_set.all()
    ]

    order_data = {
        "id": order.id,
        "customer_id": order.customer.id,
        "price": float(order.price),
        "items": items
    }

    async_to_sync(channel_layer.group_send)(
    f"customer_{order.customer.id}",
    {
        "type": "order_update",  # <-- this must match the async def order_update(self, event)
        "order": order_data
    }
)


def announce_order_update():
    orders = Order.objects.filter(picked_up=False, orderitem__product__needs_kitchen=True).distinct()

    channel_layer = get_channel_layer()
    data = []
    for order in orders:
        data.append({
            "id": order.id,
            "customer_id": order.customer.id,
            "price": float(order.price),
            "payed": order.payed,
            "items": [
                {"name": item.product.name, "quantity": item.quantity}
                for item in order.orderitem_set.filter(product__needs_kitchen=True)
            ]
        })

    async_to_sync(channel_layer.group_send)(
        "kitchen",
        {
            "type": "kitchen_update",
            "data": {
                "status": "orders_list",
                "orders": data,
            }
        }
    )
    print("announce_order_update: sent kitchen update")
