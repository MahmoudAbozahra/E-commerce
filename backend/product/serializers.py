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


class ProductPrimaryImageSerializer(serializers.Serializer):
    url = serializers.URLField()
    alt_text = serializers.CharField(allow_blank=True)


class VariantSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source="product.id", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    product_primary_image = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "sku",
            "option_values",
            "price",
            "stock",
            "low_stock_threshold",
            "is_active",
            "product_id",
            "product_name",
            "product_slug",
            "product_primary_image",
        )
        read_only_fields = ("id", "stock")

    @extend_schema_field(ProductPrimaryImageSerializer(allow_null=True))
    def get_product_primary_image(self, obj):
        images = list(getattr(obj.product, "catalog_images", ()))
        image = next((item for item in images if item.is_primary), images[0] if images else None)
        if image is None:
            return None
        request = self.context.get("request")
        url = image.image.url
        return {"url": request.build_absolute_uri(url) if request else url, "alt_text": image.alt_text}


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
    primary_image = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "brand",
            "category",
            "featured",
            "min_price",
            "available",
            "rating_average",
            "review_count",
            "primary_image",
            "variants",
        )

    @extend_schema_field(ProductPrimaryImageSerializer(allow_null=True))
    def get_primary_image(self, obj):
        images = list(getattr(obj, "catalog_images", ()))
        image = next((item for item in images if item.is_primary), images[0] if images else None)
        if image is None:
            return None
        request = self.context.get("request")
        url = image.image.url
        return {"url": request.build_absolute_uri(url) if request else url, "alt_text": image.alt_text}

    @extend_schema_field(VariantSerializer(many=True))
    def get_variants(self, obj):
        return VariantSerializer(getattr(obj, "catalog_variants", ()), many=True).data


class ProductDetailSerializer(ProductListSerializer):
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
