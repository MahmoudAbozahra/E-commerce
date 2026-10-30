from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q

# Create your models here.


class Category(models.TextChoices):
    COMPUTERS = 'Computer', 'Computers'
    PHONES = 'Phones', 'Phones'
    FOOD = 'Food', 'Food'
    HOME = 'Home', 'Home'



class Products(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(max_length=1000)
    price = models.DecimalField(max_digits=9, decimal_places=2)
    brand = models.CharField(max_length=100)
    category = models.CharField( max_length=50 ,choices=Category.choices)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=0)
    createAt = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        constraints = [models.CheckConstraint(check=Q(price__gte=0), name='product_price_nonnegative')]
        indexes = [models.Index(fields=['category', 'name'])]
     
     
    def __str__(self):
        return self.name
    
    
    
class Review(models.Model):
    product = models.ForeignKey(Products, null=True, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='reviews')
    comment = models.TextField(max_length=1000)
    rating = models.PositiveSmallIntegerField()
    createAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(rating__gte=0) & Q(rating__lte=5), name='review_rating_0_to_5'),
            models.UniqueConstraint(fields=['product', 'user'], name='unique_product_review_user'),
        ]
  
     
     
    def __str__(self):
        return self.comment
