from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Shop
from django import forms


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        labels = {
            'username': 'Username',
            'email': 'Email',
            'password1': 'Password',
            'password2': 'Confirm Password',
        }


class ShopAddForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ['name', 'sellers']

