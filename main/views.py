from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
import random
import string
from django.http import HttpResponse, HttpResponseForbidden, Http404
from .models import *
import os
from django.contrib import messages
# Create your views here.
def index(request):
    return render(request, 'index.html')


def login(request):
    return render(request, 'registration/login.html')
def AGB(request):
    return render(request, 'registration/AGB.html')

def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been created successfully')
            return redirect('login')
    return render(request, 'registration/register.html', {'form': form})


def credits(request):
    return render(request, 'credits.html')


def CreateShop(request):
    if request.method == 'POST':
        form = ShopAddForm(request.POST)
        oneTimePassword = request.POST['one-time-password']
        if oneTimePassword != open('one_time_password.txt', 'r').read():
            os.remove('one_time_password.txt')
            messages.error(request, 'Wrong one time password')
            return redirect('createShop')
        if form.is_valid():
            form.save()
            os.remove('one_time_password.txt')
            messages.success(request, 'Your Shop has been created successfully')
            return redirect('index')
    form = ShopAddForm()
    return render(request, 'createShop.html' , {'form': form})



def generate_one_time_password(request):
    if request.user.is_superuser:
        code = generate_random_string(6)
        with open('one_time_password.txt', 'w') as f:
            f.write(str(code))#
            messages.success(request, f'''
                <textarea id="otp-textarea" cols="20" rows="1" style="position:absolute;left:-9999px;">{code}</textarea>
                One time password has been generated successfully. 
                <button type="button" onclick="copyOtp()">Click to copy OTP</button>
            ''')


        return redirect('index')
    else:
        messages.error(request, 'You are not allowed to generate one time password')
        return redirect('index')
    

def generate_random_string(length):
    # Define the character sets
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special_chars = string.punctuation
    
    # Combine all character sets
    all_chars = uppercase + lowercase + digits + special_chars
    
    # Generate the random string
    random_string = ''.join(random.choice(all_chars) for _ in range(length))
    print(random_string)
    
    return random_string

# Example usage:

def help(request):
    return render(request, 'help.html')



def Shop_view(request, id = None):
    shop_instance = get_object_or_404(Shop, id=id)
    if id is None:
        messages.error(request, 'You are not allowed to access this page, please contact admin')
        return redirect('index')
    else:
        if request.user.is_authenticated:
            products = Product.objects.filter(shop=id)
            if request.user in shop_instance.sellers.all():
                products = Product.objects.filter(shop=id)
                return render(request, 'shop.html', {'products': products})
            else:
                messages.error(request, 'You are not allowed to access this page, because you are not a seller of this shop')
                return redirect('index')
        else:
            messages.error(request, 'You are not allowed to access this page, because you are not logged in')
            return redirect('index')
    

def create_product(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = ProductAddForm(request.user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your Product has been created successfully')
                return redirect('Shop', id=request.POST['shop'])
        else:
            form = ProductAddForm(request.user)
        return render(request, 'createProduct.html', {'form': form})
    else:
        messages.error(request, 'You are not allowed to access this page, because you are not logged in')
        return redirect('index')


