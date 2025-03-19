from rest_framework import serializers
from .models import Products


class productserializer(serializers.ModelSerializer):
    
   # user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Products
        fields = "__all__"
       # read_only_fields=['user']