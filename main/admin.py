from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect, get_object_or_404
from django.utils.html import format_html
from .models import Product, Order, Customers, Income, OrderItem, Shop, ShopUser, SiteStatus

# -----------------------------
# Normale Models
# -----------------------------
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Customers)
admin.site.register(Income)
admin.site.register(OrderItem)
admin.site.register(ShopUser)

# -----------------------------
# Shop Admin mit Activate Button
# -----------------------------
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
        return redirect('../../')  # Zurück zur Admin-Seite

    def activate_button(self, obj):
        if not obj.activated:
            return format_html('<a class="button" href="{}">Activate</a>', f'{obj.id}/activate/')
        return "Active"

    activate_button.short_description = 'Activate Shop'


# -----------------------------
# SiteStatus Admin mit Toggle
# -----------------------------
@admin.register(SiteStatus)
class SiteStatusAdmin(admin.ModelAdmin):
    list_display = ('maintenance_mode', 'toggle_button')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:status_id>/toggle/',
                self.admin_site.admin_view(self.toggle_status),
                name='status-toggle',
            ),
        ]
        return custom_urls + urls

    def toggle_status(self, request, status_id):
        status = get_object_or_404(SiteStatus, pk=status_id)
        status.maintenance_mode = not status.maintenance_mode
        status.save()
        state = "ON" if status.maintenance_mode else "OFF"
        self.message_user(request, f'Maintenance mode turned {state}!')
        return redirect('../../')

    def toggle_button(self, obj):
        label = "Activate" if not obj.maintenance_mode else "Deactivate"
        return format_html('<a class="button" href="{}">{}</a>', f'{obj.id}/toggle/', label)

    toggle_button.short_description = 'Toggle Maintenance'
