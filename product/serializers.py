from rest_framework import serializers

from .models import Products, Review


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'user', 'comment', 'rating', 'createAt')
        read_only_fields = ('id', 'user', 'createAt')

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value


class ProductSerializer(serializers.ModelSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Products
        fields = ('id', 'name', 'description', 'price', 'brand', 'category', 'rating', 'stock', 'createAt', 'reviews')
        read_only_fields = ('id', 'rating', 'createAt', 'reviews')

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError('Price cannot be negative.')
        return value


class ProductPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = ProductSerializer(many=True)
