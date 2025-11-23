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
        fields = ['name', 'sellers' ]



class ProductAddForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'happy_hour_price', 'shop', 'needs_kitchen' ]

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if user.is_superuser:
            queryset = Shop.objects.all()
        else:
            queryset = Shop.objects.filter(sellers=user)

        # Modify the display names
        choices = []
        for shop in queryset:
            label = shop.name
            # Add * if user is superuser but not a seller of this shop
            if user.is_superuser and user not in shop.sellers.all():
                label += ' *'
            choices.append((shop.id, label))

        self.fields['shop'].choices = choices