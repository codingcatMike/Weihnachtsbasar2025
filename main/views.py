from django.shortcuts import render, redirect
from .forms import *
import random
import string
from django.http import HttpResponse, HttpResponseForbidden, Http404
from .models import Shop
import os
# Create your views here.
def index(request):
    return render(request, 'index.html')


def login(request):
    return render(request, 'registration/login.html')


def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('registration/login.html')
    return render(request, 'registration/register.html', {'form': form})


def credits(request):
    return render(request, 'credits.html')


def CreateShop(request):
    if request.method == 'POST':
        form = ShopAddForm(request.POST)
        oneTimePassword = request.POST['one-time-password']
        if oneTimePassword != open('one_time_password.txt', 'r').read():
            os.remove('one_time_password.txt')
            return redirect('createShop')
        if form.is_valid():
            form.save()
            os.remove('one_time_password.txt')
            return redirect('index')
    form = ShopAddForm()
    return render(request, 'createShop.html' , {'form': form})



def generate_one_time_password(request):
    if request.user.is_superuser:
        with open('one_time_password.txt', 'w') as f:
            f.write(str(generate_random_string(6)))
        return redirect('createShop')
    else:
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



def get_ontime_password(request, pk):
    if not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to access this page.")
    try:
        shop = Shop.objects.get(pk=pk)
    except Shop.DoesNotExist:
        raise Http404("Shop not found.")
    # Implement the logic to generate or retrieve the ontime password for the shop
    # For demonstration, generate a random string as password
    password = generate_random_string(8)
    # You can save or log the password as needed here
    return HttpResponse(f"Ontime password for shop '{shop.name}': {password}")


def Shop(request, id = None):
    if id is not None:
        return redirect('index')
    return render(request, 'Shop.html')
