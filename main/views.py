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
from .consumers import send_orders_update, send_order_customer_update, announce_order_update # send_onscreen_order
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
from django.http import JsonResponse
import json
from collections import Counter
from django.http import JsonResponse
from collections import Counter
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from django.shortcuts import render
from django.http import JsonResponse
from .models import Customers
from django.views.decorators.csrf import csrf_exempt


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
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, height - 50, "Weihnachtsbasarprojekt 2025 Derksen")
    
    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawCentredString(width / 2, height - 65, "(NOT AN OFFICIAL RECEIPT / KEIN OFFIZIELLER KASSENZETTEL)")

    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width / 2, height - 85, f"Receipt #{order.id}")

    # Customer info
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, height - 120, f"Customer ID: {order.customer.id}")
    pdf.drawString(50, height - 135, f"Total Price: €{order.price:.2f}")

    # Table data
    data = [["Qty", "Product", "Unit Price", "Total"]]
    for item in items:
        total_item = item['quantity'] * item['price']
        data.append([item['quantity'], item['name'], f"€{item['price']:.2f}", f"€{total_item:.2f}"])
    
    # Add total row
    data.append(["", "", "TOTAL:", f"€{order.price:.2f}"])

    # Table styling
    table = Table(data, colWidths=[25*mm, 80*mm, 30*mm, 30*mm])
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
    log(f"{request.user.username} accessed {request.META.get('HTTP_REFERER', '/')} page")
    return render(request, 'registration/login.html')

def AGB(request):
    log(f"{request.user.username} accessed {request.META.get('HTTP_REFERER', '/')} page")
    return render(request, 'registration/AGB.html')

def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been created successfully')
            log(f'The User account of {form.cleaned_data["username"]} has been created successfully')
            return redirect('login')
    log(f"{request.user.username} accessed {request.META.get('HTTP_REFERER', '/')} page")
    return render(request, 'registration/register.html', {'form': form})

def credits(request):
    log(f"{request.user.username} accessed {request.META.get('HTTP_REFERER', '/')} page")
    return render(request, 'credits.html')



def CreateShop(request):
    if request.method == 'POST':
        form = ShopAddForm(request.POST)
        if form.is_valid():
            # Create the Shop object
            shop = form.save(commit=False)
            shop.save()
            
            # Add current user as ShopUser with level 3
            shop_user, created = ShopUser.objects.get_or_create(
                user=request.user,
                shop=shop,
                defaults={'level': 3}
            )

            # Delete the one-time password file if exists
            try:
                os.remove('one_time_password.txt')
            except FileNotFoundError:
                pass

            # Show success message and log
            messages.success(request, 'Your Shop has been created successfully')
            log(f'The Shop of {request.user.username} has been created successfully with name {form.cleaned_data["name"]}')

            return redirect('ShopSettings', shop.id)
        else:
            messages.error(request, 'There was an error creating your Shop. Please check the form.')

    else:
        form = ShopAddForm()

    # Log page access
    log(f"{request.user.username} accessed {request.META.get('HTTP_REFERER', '/')} page")
    return render(request, 'createShop.html', {'form': form})


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
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special_chars = string.punctuation
    all_chars = uppercase + lowercase + digits + special_chars
    random_string = ''.join(random.choice(all_chars) for _ in range(length))
    log(f'A random string of length {length} has been generated by {request.user.username}')
    return random_string

def help(request):
    log(f"{request.user.username} accessed {request.META.get('HTTP_REFERER', '/')} page")
    return render(request, 'help.html')

def Shop_view(request, id = None):
    shop_instance = get_object_or_404(Shop, id=id)
    if id is None:
        messages.error(request, 'You are not allowed to access this page, please contact admin')
        log(f"{request.user.username} tried to access shop page without id", 2)
        return redirect('index')
    else:
        if request.user.is_authenticated:
            try:
                shop_user = ShopUser.objects.get(user=request.user, shop=shop_instance)
            except:
                if request.user.is_superuser:
                    ShopUser.objects.get_or_create(user=request.user,shop=shop_instance,defaults={'level': 3})
                if request.user not in shop_instance.sellers.all():
                    messages.warning(request, 'You are not a seller of this shop, please contact admin if you think this is a mistake')
                else:
                    ShopUser.objects.get_or_create(user=request.user,shop=shop_instance,defaults={'level': 1})
                shop_user = ShopUser.objects.get(user=request.user, shop=shop_instance)
                
            if shop_user.level != 0: # Level 0
                products = Product.objects.filter(shop=id)
                if request.user in shop_instance.sellers.all() or request.user.is_superuser:
                    if request.user.is_superuser and request.user not in shop_instance.sellers.all():
                        log(f"{request.user.username} accessed shop page as superuser", 0)
                        base_url = f"{request.scheme}://{request.get_host()}"
                        link = f"{base_url}/admin/main/shop/{id}/change/"
                        msg = mark_safe(
                            f'You are accessing this page as a superuser, but you are not a seller of this shop. '
                            f'Add yourself <a href="{link}">here</a>.'
                        )
                        messages.warning(request, msg)
                    products = Product.objects.filter(shop=id)
                    log(f"{request.user.username} accessed {request.META.get('HTTP_REFERER', '/')} page")
                    return render(request, 'shop.html', {'products': products , 'shop': shop_instance})
                else:
                    messages.error(request, 'You are not allowed to access this page, because you are not a seller of this shop')
                    log(f"{request.user.username} tried to access shop page, but failed because he is not a seller of this shop", 2)
                return redirect('index')
            else: 
                messages.error(request, 'You are not allowed to access this page, because your account is locked')
                log(f"{request.user.username} tried to access shop page, but failed because his account is locked", 2)
                return redirect('index')
        else:
            messages.error(request, 'You are not allowed to access this page, because you are not logged in')
            log(f"Someone tried to access shop page, but failed because he is not logged in" , 2)
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
            log(f"{request.user.username} accessed {request.META.get('HTTP_REFERER', '/')} page")
        return render(request, 'createProduct.html', {'form': form})
    else:
        messages.error(request, 'You are not allowed to access this page, because you are not logged in')
        log(f"Someone tried to access create product page, but failed because he is not logged in", 2)
        return redirect('index')

def SendOrder(request):
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Nur POST erlaubt"}, status=405)
    
    data = json.loads(request.body)
    shop = data.get('shop')
    customer_id = data.get('customer_id')
    products = data.get('products', [])
    print('Your shop is: ' + shop)
    if not customer_id or not products:
        return JsonResponse({"status": "error", "message": "Kunden-ID oder Produkte fehlen"}, status=400)


    shop_obj = get_object_or_404(Shop, id=shop)

    if not shop_obj.activated:
        messages.error(request, "Dein Shop ist nicht aktiviert.\nWende dich an den Admin")
        return JsonResponse(
            {"status": "error", "message": "Der Shop ist nicht aktiviert"}, 
            status=400
        )


    customer, created_customer = Customers.objects.get_or_create(id=customer_id)
    order, created_order = Order.objects.get_or_create(customer=customer, defaults={"price": 0})
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

    log(f'The User account of {request.user.username} sent an order with customer id {customer_id} and products {products}')
    announce_order_update()
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
        "pay_room",
        {
            "type": "new_order",
            "orders": orders_data,
            "income": float(current_income),
        }
    )

    send_orders_update()
    print(f"[VIEW] Sending order update for customer {order.customer.id}")
    send_order_customer_update(order)
    return JsonResponse({"status": "ok", "order_id": order.id, "total": order.price})

def cash_register(request):
    if not request.user.is_staff:
        log(f"{request.user.username} tried to access cash register page, but failed because he is not a staff member", 2)
        messages.error(request, 'You are not allowed to access this page, because you are not a staff member')
        return redirect('index')

    log(f"{request.user.username} accessed {request.META.get('HTTP_REFERER', '/')} page")

    orders = Order.objects.filter(payed=False)
    current_money = sum(income.price for income in Income.objects.all())
    print(current_money)

    order = orders.first()
    if order:
        for order_item in order.orderitem_set.all():
            print("Order product quantity: ", order_item.quantity)

    return render(request, 'cash_register.html', {'orders': orders, 'income': current_money})

def pay_id(request, id):
    order = get_object_or_404(Order, id=id)
    order.payed = True
    needs_kitchen = order.products.filter(needs_kitchen=True).exists()
    if needs_kitchen == False:
        order.picked_up = True
    order.save()
    Income.objects.create(price=order.price, order=order, reason='Order')
    announce_order_update()
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "pay_screen_updates",
        {
            "type": "order_paid",
            "order_id": 0
        }
    )
    return JsonResponse({"status": "ok", "order_id": order.id})

def display_order(request, id):
    order = get_object_or_404(Order, id=id)
    url = settings.SITE_URL + reverse("receipt", args=[order.id])
    qr = qrcode.make(url)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    qr_base64 = base64.b64encode(buf.read()).decode("utf-8")
    qr_data = f"data:image/png;base64,{qr_base64}"

    order_data = {
        "id": order.id,
        "customer_id": order.customer.id,
        "price": float(order.price),
        "items": [
            {"name": i.product.name, "quantity": i.quantity, "price": float(i.product.price)}
            for i in order.orderitem_set.all()
        ],
        "qr_code": qr_data,
    }

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "pay_screen_updates",
        {
            "type": "new_onscreen",
            "order": order_data
        }
    )

    return JsonResponse({"status": "ok", "order_id": order.id})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Shop, ShopUser
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.http import require_GET

@require_GET
def search_users(request, shop_id):
    query = request.GET.get('q', '').strip()
    shop = get_object_or_404(Shop, id=shop_id)
    existing_user_ids = shop.shopuser_set.values_list('user_id', flat=True)

    if query:
        users = User.objects.filter(username__icontains=query).exclude(id__in=existing_user_ids)[:10]
        results = [{'id': u.id, 'username': u.username} for u in users]
    else:
        results = []

    return JsonResponse(results, safe=False)

LEVELS = {
    0: 'Locked',
    1: 'Seller',
    2: 'Moderator',
    3: 'Creator'
}

def get_actor_level(user, shop):
    
    """Return the level of the user in this shop."""
    if user.is_superuser:
        return 3  # Creator
    su = ShopUser.objects.filter(shop=shop, user=user).first()
    if su:
        return su.level
    return 0  # Locked / no access

def ShopSettings(request, shop_id):
    id = shop_id
    shop = get_object_or_404(Shop, id=id)
    actor_level = get_actor_level(request.user, shop)
    shop_users = ShopUser.objects.filter(shop=shop)

    # Handle shop renaming
    if request.method == 'POST' and 'rename_shop' in request.POST:
        if actor_level == 3:  # Only Creator can rename
            new_name = request.POST.get('shop_name')
            if new_name:
                shop.name = new_name
                shop.save()
                messages.success(request, "Shop renamed successfully.")
                return redirect('ShopSettings', shop_id=shop.id)
        else:
            messages.error(request, "You do not have permission to rename this shop.")
    # Handle adding seller
    if request.method == 'POST' and 'add_user_id' in request.POST:
        if actor_level >= 2:  # Only Manager or Creator can add
            user_id = request.POST.get('add_user_id')
            user_to_add = User.objects.filter(id=user_id).first()
            if user_to_add:
                ShopUser.objects.create(shop=shop, user=user_to_add, level=1)
                messages.success(request, f"User {user_to_add.username} added successfully.")
                return redirect('ShopSettings', shop_id=shop.id)


    # Handle seller removal
    if request.method == 'POST' and 'remove_seller_id' in request.POST:
        remove_id = request.POST.get('remove_seller_id')
        su_to_remove = ShopUser.objects.filter(shop=shop, user_id=remove_id).first()
        if su_to_remove and actor_level > su_to_remove.level:
            su_to_remove.delete()
            messages.success(request, "Seller removed successfully.")
            return redirect('ShopSettings', shop_id=shop.id)

    # Handle seller level change
    if request.method == 'POST' and 'user_id' in request.POST:
        su_id = request.POST.get('user_id')
        new_level = int(request.POST.get('new_level', 0))
        su_to_update = ShopUser.objects.filter(shop=shop, user_id=su_id).first()
        if su_to_update and actor_level > su_to_update.level:
            if new_level <= actor_level:
                su_to_update.level = new_level
                su_to_update.save()
                messages.success(request, "Seller level updated.")
            else:
                messages.error(request, "You cannot assign a level higher than yours.")
            return redirect('ShopSettings', shop_id=shop.id)

    # Handle Product Creation
    if request.method == 'POST' and 'create_product' in request.POST:
        form = ProductAddForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product created successfully!')
            return redirect('ShopSettings', shop_id=shop.id)
    else:
        form = ProductAddForm(request.user)

    # Precompute level names and allowed levels
    for su in shop_users:
        su.level_name = LEVELS.get(su.level, "Unknown")
        su.allowed_levels = [(lvl, name) for lvl, name in LEVELS.items() if lvl <= actor_level]

    context = {
        'shop': shop,
        'shop_users': shop_users,
        'actor_level': actor_level,
        'form': form,
    }

    return render(request, 'shop_settings.html', context)

def pay_Screen(request):
    return render(request, "pay_screen.html", {})

def receipt_pdf(request, order_id):
    buffer = generate_receipt_pdf(order_id)
    return FileResponse(buffer, as_attachment=True, filename=f"receipt_{order_id}.pdf")

def remove_from_payscreen(request):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "pay_screen_updates",
        {
            "type": "order_paid",
            "order_id": 0
        }
    )
    return JsonResponse({"status": "ok"})

@csrf_exempt
def customer(request):

    """
    Handles customer screen:
    - POST: generates a new customer ID
    - GET: optionally preloads unpaid orders if ?cid=... is passed
    """
    if request.method == "POST":
        # Generate next customer ID
        top_customer = Customers.objects.order_by('-id').first()
        next_cid = top_customer.id + 1 if top_customer else 1
        return JsonResponse({"cid": next_cid})

    # GET request
    cid = request.GET.get("cid")
    orders = []

    if cid:
        # Fetch all unpaid orders for this customer
        qs = Order.objects.filter(customer_id=cid, payed=False).prefetch_related("orderitem_set__product")
        for o in qs:
            orders.append({
                "id": o.id,
                "price": o.price,
                "customer_id": o.customer.id,
                "items": [{"name": item.product.name, "quantity": item.quantity} for item in o.orderitem_set.all()]
            })

        # If the request is AJAX, return JSON directly
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"orders": orders})

    # Otherwise, render template with preloaded orders
    return render(request, "customer.html", {"cid": cid, "orders": orders})

from .models import SiteStatus

from django.shortcuts import render, redirect
from .models import SiteStatus

MAINTENANCE_PASSWORD = "maain"

def maintenance_page(request):
    status = SiteStatus.objects.first()
    maintenance_on = status.maintenance_mode if status else False
    bypass = request.session.get('maintenance_bypass', False)

    if request.method == 'POST':
        password = request.POST.get('password', '')
        if password == MAINTENANCE_PASSWORD:
            request.session['maintenance_bypass'] = True
            bypass = True
            return redirect('/')  # Zurück zur Startseite

    context = {
        "maintenance_mode": maintenance_on,
        "bypass": bypass,
        "request": request
    }
    return render(request, '501.html', context)

def search_users(request, shop_id):
    """
    Dummy view for searching users in a shop.
    Replace with real implementation later.
    """
    return JsonResponse({"status": "not implemented yet"})

def kitchen_view(request):
    orders = Order.objects.filter(products__needs_kitchen=True, picked_up=False).distinct()
    return render(request, "kitchen.html", {"orders": orders})


def picked_up(request, id):
    order = get_object_or_404(Order, id=id)
    if order.payed == True:
        order.picked_up = True
        order.save()
        return JsonResponse({"status": "ok", "order_id": order.id})
    else:
        return JsonResponse({"status": "customer_not_payed", "order_id": order.id})
    

def site_status(request):
    site_status = SiteStatus.objects.first()
    maintenance = False
    if site_status:
        maintenance = site_status.maintenance_mode
        print(maintenance)
    return JsonResponse({"maintenance_mode": maintenance})