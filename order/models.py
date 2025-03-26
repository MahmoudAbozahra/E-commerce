from django.db import models
from operator import mod
from django.contrib.auth.models import User
from product.models import Products
# Create your models here.


class OrderStatus(models.TextChoices):
    PROCESSING = 'Processing'
    SHIPPED = 'Shipped'
    DELIVERED = 'Delivered'
    
    
    
class PaymentStatus(models.TextChoices):
    PAID = 'Paid'
    UNPAID = 'Unpaid'
    
    
class PaymentMethod(models.TextChoices):
    COD = 'cod'
    CARD = 'Card'
    
    
class Order(models.Model):
    city=models.CharField(max_length=500 , default="" , blank=False)
    zip_code=models.CharField(max_length=500 , default="" , blank=False)
    street=models.CharField(max_length=500 , default="" , blank=False)
    state=models.CharField(max_length=500 , default="Processing" , blank=False)
    country=models.CharField(max_length=500 , default="" , blank=False)
    phone_no=models.CharField(max_length=500 , default="" , blank=False)
    total_amount=models.IntegerField(default=0)
    payment_status=models.CharField(max_length=50 , choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    payment_method=models.CharField(max_length=50 , choices=PaymentMethod.choices, default=PaymentMethod.CARD)
    status=models.CharField(max_length=50 , choices=OrderStatus.choices, default=OrderStatus.PROCESSING)
    user=models.ForeignKey(User,null=True,on_delete=models.SET_NULL)
    createAt= models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self):
        return str(self.id)
    
    


class OrderItem(models.Model):
    product = models.ForeignKey(Products,null=True,on_delete=models.SET_NULL)
    order = models.ForeignKey(Order,null=True,on_delete=models.CASCADE, related_name='orderitems')
    name = models.CharField(max_length=60 , default="" ,blank=False)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=7 , decimal_places=2 ,blank=False)
    
    
    def __str__(self):
        return self.name