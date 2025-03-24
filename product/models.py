from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Category(models.TextChoices):
    COMPUTERS = 'Computer'
    PHONES = 'Phones'
    FOOD = 'Food'
    HOME = 'Home'



class Products(models.Model):
    name = models.CharField( max_length=200 , default=" " , blank=False)
    description = models.TextField( max_length=1000 , default=" " , blank=False)
    price = models.DecimalField( max_digits=7 , default=0 , decimal_places=2)
    brand = models.CharField( max_length=100 , default=" " , blank=False)
    category = models.CharField( max_length=50 ,choices=Category.choices)
    rating = models.DecimalField( max_digits=3 , default=" " , decimal_places=2)
    stock = models.IntegerField(default=0)
    createAt= models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User , null=True , on_delete=models.SET_NULL)
     
     
    def __str__(self):
        return self.name
    
    
    
class Review(models.Model):
    product = models.ForeignKey(Products , null=True , on_delete=models.CASCADE,related_name='reviews')
    user = models.ForeignKey(User , null=True , on_delete=models.SET_NULL)
    comment = models.TextField( max_length=1000 , default=" " , blank=False)
    rating = models.IntegerField(default=0)
    createAt= models.DateTimeField(auto_now_add=True)
  
     
     
    def __str__(self):
        return self.comment