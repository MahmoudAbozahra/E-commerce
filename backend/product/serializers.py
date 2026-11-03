from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Brand, Category, InventoryMovement, Product, ProductImage, ProductVariant, Review, WishlistItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        instance = self.instance or Category(**attrs)
        for key, value in attrs.items():
            setattr(instance, key, value)
        instance.clean()
        return attrs


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = "__all__"
        read_only_fields = ("id", "created_at")


class VariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ("id", "sku", "option_values", "price", "stock", "low_stock_threshold", "is_active")
        read_only_fields = ("id", "stock")


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = "__all__"


class ProductListSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    min_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    available = serializers.BooleanField(read_only=True)
    rating_average = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    review_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = ("id", "name", "slug", "brand", "category", "featured", "min_price", "available", "rating_average", "review_count")


class ProductDetailSerializer(ProductListSerializer):
    variants = VariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ("description", "variants", "images", "created_at", "updated_at")


class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class VariantWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = "__all__"
        read_only_fields = ("id", "stock", "option_signature", "created_at", "updated_at")


class InventoryAdjustmentSerializer(serializers.Serializer):
    delta = serializers.IntegerField()
    reason = serializers.CharField(max_length=100)


class InventoryMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryMovement
        fields = "__all__"
        read_only_fields = ("id", "variant", "delta", "reason", "actor", "reference", "created_at")


class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Review
        fields = ("id", "username", "rating", "comment", "is_approved", "created_at", "updated_at")
        read_only_fields = ("id", "username", "is_approved", "created_at", "updated_at")


class WishlistProductSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    min_price = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    available = serializers.BooleanField()


class WishlistSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    product_id = serializers.PrimaryKeyRelatedField(source="product", queryset=Product.objects.filter(status=Product.Status.ACTIVE), write_only=True)

    class Meta:
        model = WishlistItem
        fields = ("id", "product", "product_id", "created_at")
        read_only_fields = ("id", "created_at")

    @extend_schema_field(WishlistProductSerializer)
    def get_product(self, obj):
        variants = list(obj.product.variants.filter(is_active=True))
        return {
            "id": obj.product_id,
            "name": obj.product.name,
            "slug": obj.product.slug,
            "min_price": min((variant.price for variant in variants), default=None),
            "available": any(variant.stock > 0 for variant in variants),
        }
