from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *
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



class ProductAddForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'shop']

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['shop'].queryset = Shop.objects.filter(sellers=user)
