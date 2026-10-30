from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q

from product.models import Products

# Create your models here.


class OrderStatus(models.TextChoices):
    PROCESSING = 'Processing'
    SHIPPED = 'Shipped'
    DELIVERED = 'Delivered'
    CANCELLED = 'Cancelled'
    
    
    
class PaymentStatus(models.TextChoices):
    PAID = 'Paid'
    UNPAID = 'Unpaid'
    
    
class PaymentMethod(models.TextChoices):
    COD = 'cod'
    
    
class Order(models.Model):
    city=models.CharField(max_length=100)
    zip_code=models.CharField(max_length=20)
    street=models.CharField(max_length=255)
    state=models.CharField(max_length=100, blank=True, default="")
    country=models.CharField(max_length=100)
    phone_no=models.CharField(max_length=30)
    total_amount=models.DecimalField(max_digits=19, decimal_places=2, default=Decimal('0.00'))
    payment_status=models.CharField(max_length=50 , choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    payment_method=models.CharField(max_length=50 , choices=PaymentMethod.choices, default=PaymentMethod.COD)
    status=models.CharField(max_length=50 , choices=OrderStatus.choices, default=OrderStatus.PROCESSING)
    user=models.ForeignKey(User,null=True,on_delete=models.SET_NULL, related_name='orders')
    createAt= models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(check=Q(total_amount__gte=0), name='order_total_nonnegative')]
    
    
    def __str__(self):
        return str(self.id)
    
    


class OrderItem(models.Model):
    product = models.ForeignKey(Products,null=True,on_delete=models.SET_NULL)
    order = models.ForeignKey(Order,null=True,on_delete=models.CASCADE, related_name='orderitems')
    name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=9, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(quantity__gte=1), name='order_item_quantity_positive'),
            models.CheckConstraint(check=Q(price__gte=0), name='order_item_price_nonnegative'),
        ]
    
    
    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['cart', 'product'], name='unique_cart_product'),
            models.CheckConstraint(check=Q(quantity__gte=1), name='cart_quantity_positive'),
        ]

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"
