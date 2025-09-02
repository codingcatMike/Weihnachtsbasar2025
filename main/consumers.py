# main/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Order, Income

class PayConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "pay_updates"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
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
        self.current_order_id = None  # track which order to display

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Receive from client
    async def receive(self, text_data):
        data = json.loads(text_data)
        
        if "display_order_id" in data:
            # Client wants to display a specific order
            self.current_order_id = data["display_order_id"]
        
        if "clear_display" in data and data["clear_display"]:
            # Client wants to clear the order
            self.current_order_id = None
            await self.send(text_data=json.dumps({"order": None}))

    # Receive from server (group)
    async def new_onscreen(self, event):
        order = event["order"]
        # Only send the order if it matches current_order_id
        if self.current_order_id and order["id"] == self.current_order_id:
            await self.send(text_data=json.dumps({
                "order": order
            }))


# main/utils.py
def send_orders_update():
    channel_layer = get_channel_layer()
    orders = Order.objects.filter(payed=False)
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
        "items": items
        
    })

    async_to_sync(channel_layer.group_send)(
        "pay_updates",
        {
            "type": "new_onscreen",
            "orders": order_data,
        }
    )

