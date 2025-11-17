from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from .views import *
from django.conf import settings
import socket
from django.conf.urls.static import static
def whoami(request):
    device_name = socket.gethostname()
    return HttpResponse(device_name)

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
    path("pay/<id>/<cupon>/", pay_id, name="pay_id"),
    path("Shop/<shop_id>/settings/", ShopSettings, name="ShopSettings"),
    path('shop/<int:shop_id>/search-users/', search_users, name='search_users'),
    path("pay_Screen/", pay_Screen, name="pay_Screen"),
    path("display_order/<id>/", display_order, name="display_order"),
    path('receipt/<int:order_id>/', generate_pdf_receipt, name='receipt'),
    path("admin/", admin.site.urls, name="admin"),
    path("rmfps/", remove_from_payscreen, name="rmfps"),
    path("customer", customer, name="customer"),
    path("kitchen/", kitchen_view, name="kitchen" ),
    path("pick_up/<id>/", picked_up, name="pick_up"),
    path("api/site-status/", site_status, name="site-status"),
    path("thh/", togglehappyhour, name="thh"),
    path('501/', maintenance_page, name='maintenance-page'),
    path("pay_sb_costs/", pay_sb_costs, name="pay_sb_costs"),
    path("generate-cupons/", generate_cupons, name="generate_cupons"),
    path("whoami/", whoami, name="whoami"),
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT, "show_indexes": True}),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

