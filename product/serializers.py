from rest_framework import serializers
from .models import *


class ProductSerializer(serializers.ModelSerializer):
    
   # user = serializers.StringRelatedField(read_only=True)
   reviews = serializers.SerializerMethodField(method_name='get_review',read_only=True)
    
   class Meta:
        model = Products
        fields = "__all__"
       # read_only_fields=['user']
       
   def get_review(self,obj):
           reviews = obj.reviews.all()
           serializer=ReviewSerializer(reviews,many=True)
           return serializer.data
       
       
class ReviewSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Review
        fields = "__all__"
       