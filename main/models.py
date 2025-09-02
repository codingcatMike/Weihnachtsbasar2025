from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=50)
    price = models.FloatField()
    shop = models.ForeignKey("Shop", on_delete=models.CASCADE)

    def __str__(self):
        return self.name + " for " + str(self.price)
    


class Shop(models.Model):
    name = models.CharField(max_length=50)
    sellers = models.ManyToManyField(User)

    def __str__(self):
        return self.name

class Customers(models.Model):
    id = models.AutoField(primary_key=True)




class Order(models.Model):
    customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True)
    price = models.FloatField() # Dieser Preis sollte die Summe der Produktpreise * Mengen sein
    payed = models.BooleanField(default=False)

    # Hier verwenden wir das Zwischenmodell "OrderItem"

    products = models.ManyToManyField(Product, through='OrderItem')

    def __str__(self):
        return f"Order {self.id} by {self.customer.id}"
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1) # Die Menge des Produkts in dieser Bestellung

    @property
    def total(self):
        return self.product.price * self.quantity

    class Meta:
        # Stellt sicher, dass ein Produkt in einer Bestellung nur einmal vorkommt
        unique_together = ('order', 'product')

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order {self.order.id}"




class Income(models.Model):
    price = models.FloatField()
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    reason = models.CharField(max_length=50)
    time = models.DateTimeField(auto_now_add=True)


            