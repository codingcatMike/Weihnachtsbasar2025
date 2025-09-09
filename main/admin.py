from django.contrib import admin
from .models import *
from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect, get_object_or_404
from django.utils.html import format_html


admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Customers)
admin.site.register(Income)
admin.site.register(OrderItem)
# admin.py
@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'activated', 'activate_button')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:shop_id>/activate/',
                self.admin_site.admin_view(self.activate_shop),
                name='shop-activate',
            ),
        ]
        return custom_urls + urls

    def activate_shop(self, request, shop_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        shop.activated = True
        shop.save()
        self.message_user(request, f'Shop "{shop.name}" activated!')
        return redirect(f'../../')  # Redirect back to change page

    def activate_button(self, obj):
        if not obj.activated:
            return format_html(
                '<a class="button" href="{}">Activate</a>',
                f'{obj.id}/activate/'
            )
        return "Active"
    activate_button.short_description = 'Activate Shop'
    activate_button.allow_tags = True
