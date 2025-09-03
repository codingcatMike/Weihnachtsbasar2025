from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
import random
import string
from django.http import HttpResponse, HttpResponseForbidden, Http404
from .models import *
import os
from django.contrib import messages
from .log import log
import json
from collections import Counter
from django.utils.safestring import mark_safe
from .consumers import send_orders_update # send_onscreen_order
from django.http import FileResponse
from .utils import generate_receipt_pdf
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from .models import Order
import io
import base64
import qrcode
from django.conf import settings
from django.urls import reverse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import JsonResponse
from .models import Order
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import mm

def generate_pdf_receipt(request, order_id):
    order = Order.objects.get(id=order_id)
    items = [
        {"name": item.product.name, "quantity": item.quantity, "price": float(item.product.price)}
        for item in order.orderitem_set.all()
    ]

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="receipt_{order.id}.pdf"'

    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Header
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(width / 2, height - 50, "🛍️ My Shop Receipt")
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width / 2, height - 70, f"Receipt #{order.id}")

    # Customer info
    pdf.drawString(50, height - 110, f"Customer ID: {order.customer.id}")
    pdf.drawString(50, height - 125, f"Total Price: ${order.price:.2f}")

    # Table data
    data = [["Qty", "Product", "Unit Price", "Total"]]
    for item in items:
        total_item = item['quantity'] * item['price']
        data.append([item['quantity'], item['name'], f"${item['price']:.2f}", f"${total_item:.2f}"])

    # Add total row
    data.append(["", "", "TOTAL:", f"${order.price:.2f}"])

    table = Table(data, colWidths=[30*mm, 70*mm, 30*mm, 30*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (0,-1), (-1,-1), colors.whitesmoke),
    ]))

    # Position table
    table.wrapOn(pdf, width, height)
    table.drawOn(pdf, 50, height - 300)

    pdf.showPage()
    pdf.save()

    return response

def index(request):
    log(f"{request.user.username} accessed {request.META.get('HTTP_REFERER', '/')} page")
    
    shops = Shop.objects.all()
    user_shops = Shop.objects.filter(sellers=request.user) if request.user.is_authenticated else []

    shops_with_marker = []
    for shop in shops:
        name = shop.name
        if request.user.is_superuser and request.user not in shop.sellers.all():
            name += " *"
        shops_with_marker.append({'shop': shop, 'display_name': name})

    context = {
        'shops': shops,
        'user_shops': user_shops,
        'marker_shops': shops_with_marker,
    }
    return render(request, 'index.html', context)



def login(request):
    log(f'{request.user.username} accessed {request.META.get('HTTP_REFERER', '/')} page')
    return render(request, 'registration/login.html')
def AGB(request):
    log(f'{request.user.username} accessed {request.META.get('HTTP_REFERER', '/')} page')
    return render(request, 'registration/AGB.html')

def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been created successfully')
            log(f'The User account of {form.cleaned_data["username"]} has been created successfully')
            return redirect('login')
    log(f'{request.user.username} accessed {request.META.get('HTTP_REFERER', '/')} page')
    return render(request, 'registration/register.html', {'form': form})


def credits(request):
    log(f'{request.user.username} accessed {request.META.get('HTTP_REFERER', '/')} page')
    return render(request, 'credits.html')


def CreateShop(request):
    if request.method == 'POST':
        form = ShopAddForm(request.POST)
        oneTimePassword = request.POST['one-time-password']
        if oneTimePassword != open('one_time_password.txt', 'r').read():
            os.remove('one_time_password.txt')
            messages.error(request, 'Wrong one time password')
            log(f'The User account of {request.user.username} tried to create a Shop with wrong one time password', 2)
            return redirect('createShop')
        if form.is_valid():
            form.save()
            os.remove('one_time_password.txt')
            messages.success(request, 'Your Shop has been created successfully')
            log(f'The Shop of {request.user.username} has been created successfully with name {form.cleaned_data["name"]}')
            return redirect('index')
    form = ShopAddForm()
    log(f'{request.user.username} accessed {request.META.get('HTTP_REFERER', '/')} page')
    return render(request, 'createShop.html' , {'form': form})



def generate_one_time_password(request):
    if request.user.is_superuser:
        code = generate_random_string(6, request)
        with open('one_time_password.txt', 'w') as f:
            f.write(str(code))#
            messages.success(request, f'''
                <textarea id="otp-textarea" cols="20" rows="1" style="position:absolute;left:-9999px;">{code}</textarea>
                One time password has been generated successfully. 
                <button type="button" onclick="copyOtp()">Click to copy OTP</button>
            ''')

        log(f'The User account of {request.user.username} generated one time password')
        return redirect('index')
    else:
        messages.error(request, 'You are not allowed to generate one time password')
        log(f'The User account of {request.user.username} tried to generate one time password, but failed because he is not admin' , 2)
        return redirect('index')
    

def generate_random_string(length, request):
    # Define the character sets
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special_chars = string.punctuation
    
    # Combine all character sets
    all_chars = uppercase + lowercase + digits + special_chars
    
    # Generate the random string
    random_string = ''.join(random.choice(all_chars) for _ in range(length))
    log(f'A random string of length {length} has been generated by {request.user.username}')
    
    return random_string

# Example usage:

def help(request):
    log(f'{request.user.username} accessed {request.META.get('HTTP_REFERER', '/')} page')
    return render(request, 'help.html')



def Shop_view(request, id = None):
    shop_instance = get_object_or_404(Shop, id=id)
    if id is None:
        messages.error(request, 'You are not allowed to access this page, please contact admin')
        log(f'{request.user.username} tried to access shop page without id', 2)
        return redirect('index')
    else:
        if request.user.is_authenticated:
            products = Product.objects.filter(shop=id)
            if request.user in shop_instance.sellers.all() or request.user.is_superuser:
                if request.user.is_superuser and request.user not in shop_instance.sellers.all():
                    log(f'{request.user.username} accessed shop page as superuser', 0)
                    base_url = f"{request.scheme}://{request.get_host()}"
                    link = f"{base_url}/admin/main/shop/{id}/change/"
                    msg = mark_safe(
                        f'You are accessing this page as a superuser, but you are not a seller of this shop. '
                        f'Add yourself <a href="{link}">here</a>.'
                    )
                    messages.warning(request, msg)
                products = Product.objects.filter(shop=id)
                log(f'{request.user.username} accessed {request.META.get('HTTP_REFERER', '/')} page')
                return render(request, 'shop.html', {'products': products , 'shop': shop_instance})
            else:
                messages.error(request, 'You are not allowed to access this page, because you are not a seller of this shop')
                log(f'{request.user.username} tried to access shop page, but failed because he is not a seller of this shop', 2)
                return redirect('index')
        else:
            messages.error(request, 'You are not allowed to access this page, because you are not logged in')
            log(f'Someone tried to access shop page, but failed because he is not logged in' , 2)
            return redirect('index')
    

def create_product(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = ProductAddForm(request.user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your Product has been created successfully')
                log(f'The Product of {request.user.username} has been created successfully with name {form.cleaned_data["name"]}')
                return redirect('Shop', id=request.POST['shop'])
        else:
            form = ProductAddForm(request.user)
            log(f'{request.user.username} accessed {request.META.get('HTTP_REFERER', '/')} page')
        return render(request, 'createProduct.html', {'form': form})
    else:
        messages.error(request, 'You are not allowed to access this page, because you are not logged in')
        log(f'Someone tried to access create product page, but failed because he is not logged in', 2)
        return redirect('index')


from django.http import JsonResponse
import json
from collections import Counter

from django.http import JsonResponse
from collections import Counter
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json

def SendOrder(request):
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Nur POST erlaubt"}, status=405)

    data = json.loads(request.body)
    customer_id = data.get('customer_id')
    products = data.get('products', [])

    if not customer_id or not products:
        return JsonResponse({"status": "error", "message": "Kunden-ID oder Produkte fehlen"}, status=400)

    # Customer und Order abrufen oder erstellen
    customer, created_customer = Customers.objects.get_or_create(id=customer_id)
    order, created_order = Order.objects.get_or_create(customer=customer, defaults={"price": 0})

    # Produkte zählen und OrderItems erstellen/aktualisieren
    counter = Counter(products)
    total_price = 0

    for product_id, quantity in counter.items():
        product = Product.objects.get(id=product_id)

        order_item, created_item = OrderItem.objects.get_or_create(
            order=order,
            product=product,
            defaults={"quantity": quantity}
        )
        if not created_item:
            order_item.quantity += quantity
            order_item.save()

        total_price += product.price * quantity

    order.price += total_price
    order.save()

    # Loggen
    log(f'The User account of {request.user.username} sent an order with customer id {customer_id} and products {products}')

    # Live-Update an Cash-Register Clients
    channel_layer = get_channel_layer()

    orders_data = [
        {
            "id": o.id,
            "customer_id": o.customer.id,
            "price": float(o.price),
            "items": [
                {"name": item.product.name, "quantity": item.quantity}
                for item in o.orderitem_set.all()
            ]
        }
        for o in Order.objects.all()
    ]

    current_income = sum(o.price for o in Order.objects.all())

    async_to_sync(channel_layer.group_send)(
        "pay_room",  # Name der Gruppe für Cash-Register-Clients
        {
            "type": "new_order",
            "orders": orders_data,
            "income": float(current_income),
        }
    )
    
    send_orders_update()    

    # Response an den Client
    return JsonResponse({"status": "ok", "order_id": order.id, "total": order.price})




def cash_register(request):
    if not request.user.is_staff:
        log(f'{request.user.username} tried to access cash register page, but failed because he is not a staff member', 2)
        messages.error(request, 'You are not allowed to access this page, because you are not a staff member')
        return redirect('index')

    log(f'{request.user.username} accessed {request.META.get("HTTP_REFERER", "/")} page')

    orders = Order.objects.filter(payed=False)
    current_money = sum(income.price for income in Income.objects.all())
    print(current_money)

    order = orders.first()
    if order:  # nur wenn eine Bestellung existiert
        for order_item in order.orderitem_set.all():
            print("Order product quantity: ", order_item.quantity)

    return render(request, 'cash_register.html', {'orders': orders, 'income': current_money})

def pay_id(request, id):
    order = get_object_or_404(Order, id=id)
    order.payed = True
    order.save()

    # Optional: record income
    Income.objects.create(price=order.price, order=order, reason='Order')

    # Notify pay screen to remove order
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "pay_screen_updates",  # MUST match PayScreenConsumer.group_name
        {
            "type": "order_paid",
            "order_id": 0
        }
    )

    return JsonResponse({"status": "ok", "order_id": order.id})

def display_order(request, id):
    order = get_object_or_404(Order, id=id)

    # QR-Code URL zur PDF-Receipt
    url = settings.SITE_URL + reverse("receipt", args=[order.id])
    
    qr = qrcode.make(url)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    qr_base64 = base64.b64encode(buf.read()).decode("utf-8")
    qr_data = f"data:image/png;base64,{qr_base64}"  # Base64-String für img src

    # Order-Daten inkl. QR-Code
    order_data = {
        "id": order.id,
        "customer_id": order.customer.id,
        "price": float(order.price),
        "items": [
            {"name": i.product.name, "quantity": i.quantity, "price": float(i.product.price)}
            for i in order.orderitem_set.all()
        ],
        "qr_code": qr_data,  # <-- hier einfügen
    }

    # Sende an WebSocket-Gruppe
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "pay_screen_updates",
        {
            "type": "new_onscreen",
            "order": order_data
        }
    )

    return JsonResponse({"status": "ok", "order_id": order.id})


def ShopSettings(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)

    if request.method == "POST":

        # Update shop name
        if "update_name" in request.POST:
            new_name = request.POST.get("shop_name")
            if new_name and new_name != shop.name:
                shop.name = new_name
                shop.save()
                messages.success(request, f"Shop name updated to '{new_name}'.")

        # Add seller
        if "add_seller" in request.POST:
            username = request.POST.get("username")
            if username:
                try:
                    user = User.objects.get(username=username)
                    if user in shop.sellers.all():
                        messages.warning(request, f"{user.username} is already a seller of this shop.")
                    else:
                        shop.sellers.add(user)
                        messages.success(request, f"{user.username} was added as a seller.")
                except User.DoesNotExist:
                    messages.error(request, f"User '{username}' does not exist.")

        # Remove seller
        if "remove_seller_id" in request.POST:
            seller_id = request.POST.get("remove_seller_id")
            try:
                user = User.objects.get(id=seller_id)
                shop.sellers.remove(user)
                messages.success(request, f"{user.username} removed from sellers.")
            except User.DoesNotExist:
                messages.error(request, "Seller not found.")

        # Remove product
        if "remove_product_id" in request.POST:
            product_id = request.POST.get("remove_product_id")
            try:
                product = Product.objects.get(id=product_id, shop=shop)
                product.delete()
                messages.success(request, f"Product '{product.name}' deleted.")
            except Product.DoesNotExist:
                messages.error(request, "Product not found.")

        # Update product price
        if "update_price" in request.POST:
            product_id = request.POST.get("product_id")
            price = request.POST.get("price")
            try:
                product = Product.objects.get(id=product_id, shop=shop)
                product.price = float(price)
                product.save()
                messages.success(request, f"Price for '{product.name}' updated to ${price}.")
            except Product.DoesNotExist:
                messages.error(request, "Product not found.")
            except ValueError:
                messages.error(request, "Invalid price entered.")

        return redirect("ShopSettings", shop_id=shop.id)

    context = {"shop": shop}
    return render(request, "shop_settings.html", context)


def pay_Screen(request):
    return render(request, "pay_Screen.html", {})

def receipt_pdf(request, order_id):
    buffer = generate_receipt_pdf(order_id)
    return FileResponse(buffer, as_attachment=True, filename=f"receipt_{order_id}.pdf")