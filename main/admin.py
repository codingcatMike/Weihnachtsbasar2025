from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Shop


admin.site.register(Shop)

