from decimal import Decimal

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from account.models import Address
from product.models import ProductVariant
from product.serializers import VariantSerializer

from .models import (
    Cart,
    CartItem,
    Coupon,
    LoyaltyTransaction,
    LoyaltyWallet,
    Order,
    OrderItem,
    OrderStatusHistory,
    Payment,
    Refund,
    ReturnRequest,
    ReturnStatusHistory,
    ShippingMethod,
    ShippingZone,
)


class CartItemSerializer(serializers.ModelSerializer):
    variant = VariantSerializer(read_only=True)
    variant_id = serializers.PrimaryKeyRelatedField(source="variant", queryset=ProductVariant.objects.filter(is_active=True), write_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ("id", "variant", "variant_id", "quantity", "line_total")

    @extend_schema_field(serializers.DecimalField(max_digits=14, decimal_places=2))
    def get_line_total(self, obj):
        return (obj.variant.price * obj.quantity).quantize(Decimal("0.01"))

    def validate(self, attrs):
        variant = attrs.get("variant") or self.instance.variant
        quantity = attrs.get("quantity", getattr(self.instance, "quantity", 0))
        if not variant.is_active or variant.product.status != variant.product.Status.ACTIVE:
            raise serializers.ValidationError({"variant_id": "Variant is unavailable."})
        if quantity > variant.stock:
            raise serializers.ValidationError({"quantity": "Requested quantity exceeds stock."})
        return attrs


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ("id", "items", "subtotal", "updated_at")

    @extend_schema_field(serializers.DecimalField(max_digits=14, decimal_places=2))
    def get_subtotal(self, obj):
        return sum((item.variant.price * item.quantity for item in obj.items.all()), Decimal("0.00"))


class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = "__all__"


class ShippingZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingZone
        fields = "__all__"


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = "__all__"
        read_only_fields = ("id", "created_at")

    def validate(self, attrs):
        instance = self.instance
        kind = attrs.get("kind", getattr(instance, "kind", None))
        value = attrs.get("value", getattr(instance, "value", None))
        valid_from = attrs.get("valid_from", getattr(instance, "valid_from", None))
        valid_to = attrs.get("valid_to", getattr(instance, "valid_to", None))
        if kind == Coupon.Kind.PERCENT and value is not None and value > 100:
            raise serializers.ValidationError({"value": "Percentage coupons cannot exceed 100%."})
        if valid_from and valid_to and valid_to <= valid_from:
            raise serializers.ValidationError({"valid_to": "Must be later than valid_from."})
        return attrs


class QuoteRequestSerializer(serializers.Serializer):
    address_id = serializers.PrimaryKeyRelatedField(source="address", queryset=Address.objects.none())
    shipping_method_id = serializers.PrimaryKeyRelatedField(source="shipping_method", queryset=ShippingMethod.objects.filter(is_active=True))
    coupon_code = serializers.CharField(required=False, allow_blank=True, default="")
    points = serializers.IntegerField(required=False, min_value=0, default=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            self.fields["address_id"].queryset = Address.objects.filter(user=request.user)


class CheckoutRequestSerializer(QuoteRequestSerializer):
    pass


class QuoteSerializer(serializers.Serializer):
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2)
    coupon_discount = serializers.DecimalField(max_digits=14, decimal_places=2)
    points = serializers.IntegerField()
    points_discount = serializers.DecimalField(max_digits=14, decimal_places=2)
    shipping_fee = serializers.DecimalField(max_digits=14, decimal_places=2)
    tax = serializers.DecimalField(max_digits=14, decimal_places=2)
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
    currency = serializers.CharField()
    disclaimer = serializers.CharField()


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"


class TimelineSerializer(serializers.ModelSerializer):
    actor = serializers.StringRelatedField()

    class Meta:
        model = OrderStatusHistory
        fields = "__all__"


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ("id", "order", "method", "status", "amount", "currency", "transaction_reference", "collected_at", "created_at", "updated_at")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = tuple(field.name for field in Order._meta.fields)


class TransitionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500)


class CouponValidateSerializer(serializers.Serializer):
    code = serializers.CharField()
    address_id = serializers.PrimaryKeyRelatedField(source="address", queryset=Address.objects.none())
    shipping_method_id = serializers.PrimaryKeyRelatedField(source="shipping_method", queryset=ShippingMethod.objects.filter(is_active=True))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            self.fields["address_id"].queryset = Address.objects.filter(user=request.user)


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyWallet
        fields = "__all__"
        read_only_fields = ("id", "user", "available_points", "outstanding_clawback", "updated_at")


class LoyaltyTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyTransaction
        fields = "__all__"
        read_only_fields = ("id", "wallet", "delta", "kind", "event_key", "order", "metadata", "created_at")


class LoyaltyAdjustmentSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)
    delta = serializers.IntegerField()
    reason = serializers.CharField(max_length=300)


class ReturnRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnRequest
        fields = "__all__"
        read_only_fields = ("id", "user", "status", "staff_note", "inventory_restored", "refund_amount", "created_at", "updated_at")

    def validate(self, attrs):
        item = attrs["order_item"]
        request = self.context["request"]
        if item.order.user_id != request.user.id or item.order.status != Order.Status.DELIVERED:
            raise serializers.ValidationError("Only your delivered order items can be returned.")
        prior = (
            item.returns.exclude(status=ReturnRequest.Status.REJECTED).aggregate(total=__import__("django.db.models", fromlist=["Sum"]).Sum("quantity"))[
                "total"
            ]
            or 0
        )
        if prior + attrs["quantity"] > item.quantity:
            raise serializers.ValidationError({"quantity": "Return quantity exceeds purchased quantity."})
        return attrs


class ReturnTimelineSerializer(serializers.ModelSerializer):
    actor = serializers.StringRelatedField()

    class Meta:
        model = ReturnStatusHistory
        fields = "__all__"


class ReturnDecisionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=(ReturnRequest.Status.APPROVED, ReturnRequest.Status.REJECTED))
    staff_note = serializers.CharField(required=False, allow_blank=True)


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = "__all__"
        read_only_fields = ("id", "return_request", "payment", "amount", "currency", "status", "reference", "completed_at", "created_at")
