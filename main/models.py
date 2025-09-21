from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    name = models.CharField(max_length=50)
    price = models.FloatField()
    happy_hour_price = models.FloatField()
    needs_kitchen = models.BooleanField(default=False)
    shop = models.ForeignKey("Shop", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} for {self.price}"


class SiteStatus(models.Model):
    maintenance_mode = models.BooleanField(default=False)

    def __str__(self):
        return f"Maintenance mode: {self.maintenance_mode}"


class Shop(models.Model):
    name = models.CharField(max_length=50)
    old_sellers = models.ManyToManyField(User, related_name='shops')
    sellers = models.ManyToManyField(User, related_name='new_shops', blank=True, through='ShopUser')
    activated = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Customers(models.Model):
    id = models.AutoField(primary_key=True)

    def __str__(self):
        return f"Customer {self.id}"


class Order(models.Model):

    customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True)
    price = models.FloatField()
    payed = models.BooleanField(default=False)
    picked_up = models.BooleanField(default=False)
    products = models.ManyToManyField(Product, through='OrderItem')
    cupon = models.ForeignKey('Cupon', null=True, blank=True, on_delete=models.SET_NULL)


    def __str__(self):
        return f"Order {self.id} by Customer {self.customer.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price_at_order = models.FloatField(default=0)  # store price at the moment of ordering

    @property
    def total(self):
        return self.price_at_order * self.quantity

    class Meta:
        unique_together = ('order', 'product')

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order {self.order.id}"



class Income(models.Model):
    price = models.FloatField()
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    reason = models.CharField(max_length=50)
    time = models.DateTimeField(auto_now_add=True)


class ShopUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    level = models.IntegerField(default=1)  # 0 = Locked | 1 = Seller | 2 = Manager | 3 = Creator

    class Meta:
        unique_together = ("user", "shop")
        db_table = "main_shopuser"

    def __str__(self):
        return f"{self.user.username} in {self.shop.name} (Level {self.level})"

class HappyHour(models.Model):
    status = models.BooleanField(default=False)


import string
import random
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver


def generate_random_cupon():
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(chars, k=3))
        # Check that there is at least one letter
        if any(c.isalpha() for c in code):
            return code


class Cupon(models.Model):
    percentage = models.IntegerField()
    used = models.BooleanField(default=False)
    data = models.CharField(max_length=20, blank=True, unique=True)

    def __str__(self):
        return f"Cupon {self.data} ({self.percentage}%)"

@receiver(pre_save, sender=Cupon)
def ensure_unique_cupon(sender, instance, **kwargs):
    if not instance.data:
        while True:
            code = generate_random_cupon()
            if not Cupon.objects.filter(data=code).exists():
                instance.data = code
                break
