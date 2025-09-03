# main/utils.py
import io
import base64
import qrcode
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.urls import reverse
from .models import Order, Income
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from .models import Order


# ------------------ QR Code Generator ------------------
def generate_order_qr_base64(order_id):
    """Generate a base64 QR code pointing to the receipt URL."""
    url = settings.SITE_URL + reverse("receipt_pdf", args=[order_id])
    qr = qrcode.make(url)

    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"


# ------------------ Send all unpaid orders ------------------
def send_orders_update():
    channel_layer = get_channel_layer()
    orders = Order.objects.filter(payed=False)
    incomes = Income.objects.all()
    income_money = sum(income.price for income in incomes)
    orders_data = []

    for order in orders:
        items = [
            {"name": item.product.name, "quantity": item.quantity, "price": item.product.price}
            for item in order.orderitem_set.all()
        ]
        orders_data.append({
            "id": order.id,
            "customer_id": order.customer.id,
            "price": order.price,
            "items": items,
            "qr_code": generate_order_qr_base64(order.id),  # QR code included
        })

    async_to_sync(channel_layer.group_send)(
        "pay_updates",
        {
            "type": "new_order",
            "orders": orders_data,
            "income_money": income_money
        }
    )


# ------------------ Send single order to on-screen display ------------------
def get_new_onscreen_order(order_id):
    channel_layer = get_channel_layer()
    order = Order.objects.get(id=order_id)
    items = [
        {"name": item.product.name, "quantity": item.quantity, "price": item.product.price}
        for item in order.orderitem_set.all()
    ]

    order_data = {
        "id": order.id,
        "customer_id": order.customer.id,
        "price": order.price,
        "items": items,
        "qr_code": generate_order_qr_base64(order.id),  # QR code included
    }

    async_to_sync(channel_layer.group_send)(
    "pay_updates",
    {
        "type": "new_onscreen",
        "order": order_data,  # ✅ correct key
    }
)


def generate_receipt_pdf(order_id):
    order = Order.objects.get(id=order_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{order_id}.pdf"'

    p = canvas.Canvas(response)
    y = 800
    p.drawString(100, y, f"Receipt for Order {order.id}")
    y -= 20
    for item in order.orderitem_set.all():
        p.drawString(100, y, f"{item.quantity} x {item.product.name} - {item.total}€")
        y -= 20
    p.drawString(100, y-20, f"Total: {order.price}€")
    p.showPage()
    p.save()
    return response


import qrcode
from io import BytesIO
from django.http import HttpResponse

def generate_qr_code_new(order_id):
    url = f"http://127.0.0.1:8000/receipt/{order_id}/"  # Link zur PDF-Seite
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer