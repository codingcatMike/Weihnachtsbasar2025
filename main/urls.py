"""
URL configuration for Basar project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", index, name="index"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/signup/", register, name="signup"),
    path("credits/", credits, name="credits"),
    path("help/", help, name="help"),
    path("get-onetime-password/", generate_one_time_password, name="get-onetime-password"),
    path("create-shop/", CreateShop, name="createShop"),
    path("AGB/", AGB, name="AGB"),
    path("Shop/<id>/", Shop_view, name="Shop"),
    path("Shop/", Shop_view, name="Shop"),
    path("create-product/", create_product, name="create_product"),
    path("SendOrder/", SendOrder, name="sendOrder"),
    path("pay/", cash_register, name="cash_register"),
    path("pay/<id>/", pay_id, name="pay_id"),
    path("Shop/<shop_id>/settings/", ShopSettings, name="ShopSettings"),
    path("pay_Screen/", pay_Screen, name="pay_Screen"),
    path("display_order/<id>/", display_order, name="display_order"),
    path('receipt/<int:order_id>/', generate_pdf_receipt, name='receipt'),
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT, "show_indexes": True}),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

