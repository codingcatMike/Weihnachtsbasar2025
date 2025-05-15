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



