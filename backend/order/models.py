import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import F, Q

from product.models import Category, Product, ProductVariant


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")
    updated_at = models.DateTimeField(auto_now=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("cart", "variant"), name="unique_cart_variant"),
            models.CheckConstraint(condition=Q(quantity__gte=1), name="cart_quantity_positive"),
        ]


class ShippingZone(models.Model):
    name = models.CharField(max_length=120, unique=True)
    countries = models.JSONField(default=list)
    states = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)


class ShippingMethod(models.Model):
    zone = models.ForeignKey(ShippingZone, on_delete=models.PROTECT, related_name="methods")
    name = models.CharField(max_length=120)
    code = models.SlugField(max_length=80, unique=True)
    flat_fee = models.DecimalField(max_digits=12, decimal_places=2)
    estimated_days_min = models.PositiveSmallIntegerField(default=1)
    estimated_days_max = models.PositiveSmallIntegerField(default=5)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(flat_fee__gte=0), name="shipping_fee_nonnegative")]


class Coupon(models.Model):
    class Kind(models.TextChoices):
        FIXED = "fixed", "Fixed"
        PERCENT = "percent", "Percent"

    code = models.CharField(max_length=40, unique=True)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    max_discount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    minimum_subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    total_limit = models.PositiveIntegerField(null=True, blank=True)
    per_user_limit = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    products = models.ManyToManyField(Product, blank=True, related_name="coupons")
    categories = models.ManyToManyField(Category, blank=True, related_name="coupons")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(value__gt=0), name="coupon_value_positive"),
            models.CheckConstraint(condition=Q(minimum_subtotal__gte=0), name="coupon_minimum_nonnegative"),
            models.CheckConstraint(condition=Q(valid_to__gt=F("valid_from")), name="coupon_window_valid"),
            models.CheckConstraint(condition=Q(kind="fixed") | Q(value__lte=100), name="coupon_percentage_at_most_100"),
        ]

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        RETURNED = "returned", "Returned"

    reference = models.CharField(max_length=24, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    currency = models.CharField(max_length=3, default="EGP")
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    coupon_discount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    points_discount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    shipping_fee = models.DecimalField(max_digits=14, decimal_places=2)
    tax = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=14, decimal_places=2)
    points_redeemed = models.PositiveIntegerField(default=0)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.PROTECT, related_name="orders")
    shipping_method = models.ForeignKey(ShippingMethod, null=True, on_delete=models.PROTECT, related_name="orders")
    shipping_method_name = models.CharField(max_length=120)
    shipping_address = models.JSONField()
    inventory_restored = models.BooleanField(default=False)
    coupon_released = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(condition=Q(total__gte=0), name="order_total_nonnegative"),
            models.CheckConstraint(condition=Q(subtotal__gte=0), name="order_subtotal_nonnegative"),
        ]

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"ORD-{uuid.uuid4().hex[:16].upper()}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, null=True, on_delete=models.SET_NULL, related_name="order_items")
    product_name = models.CharField(max_length=200)
    sku = models.CharField(max_length=64)
    option_values = models.JSONField(default=dict)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gte=1), name="order_item_quantity_positive"),
            models.CheckConstraint(condition=Q(unit_price__gte=0, line_total__gte=0), name="order_item_money_nonnegative"),
        ]


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="timeline")
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, choices=Order.Status.choices)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    note = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")


class CheckoutAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="checkout_attempts")
    key = models.CharField(max_length=100)
    request_hash = models.CharField(max_length=64)
    order = models.OneToOneField(Order, null=True, blank=True, on_delete=models.CASCADE, related_name="checkout_attempt")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("user", "key"), name="unique_user_checkout_key")]


class CouponRedemption(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.PROTECT, related_name="redemptions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="coupon_redemptions")
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="coupon_redemption")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    released_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class LoyaltyWallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="loyalty_wallet")
    available_points = models.PositiveIntegerField(default=0)
    outstanding_clawback = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)


class LoyaltyTransaction(models.Model):
    class Kind(models.TextChoices):
        EARN = "earn", "Earn"
        REDEEM = "redeem", "Redeem"
        REVERSE = "reverse", "Reverse"
        ADJUST = "adjust", "Adjust"

    wallet = models.ForeignKey(LoyaltyWallet, on_delete=models.PROTECT, related_name="transactions")
    delta = models.IntegerField()
    kind = models.CharField(max_length=12, choices=Kind.choices)
    event_key = models.CharField(max_length=120, unique=True)
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.PROTECT, related_name="loyalty_transactions")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class Payment(models.Model):
    class Method(models.TextChoices):
        COD = "cod", "Cash on delivery"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        PARTIALLY_REFUNDED = "partially_refunded", "Partially refunded"
        REFUNDED = "refunded", "Refunded"

    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="payments")
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.COD)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default="EGP")
    transaction_reference = models.CharField(max_length=120, unique=True)
    collected_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ReturnRequest(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        COMPLETED = "completed", "Completed"

    order_item = models.ForeignKey(OrderItem, on_delete=models.PROTECT, related_name="returns")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="returns")
    quantity = models.PositiveIntegerField()
    reason = models.TextField(max_length=1000)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    staff_note = models.TextField(blank=True)
    inventory_restored = models.BooleanField(default=False)
    refund_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(quantity__gte=1), name="return_quantity_positive")]


class ReturnStatusHistory(models.Model):
    return_request = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name="timeline")
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, choices=ReturnRequest.Status.choices)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    note = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")


class Refund(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending cash refund"
        COMPLETED = "completed", "Cash refund completed"
        REJECTED = "rejected", "Rejected"

    return_request = models.OneToOneField(ReturnRequest, on_delete=models.PROTECT, related_name="refund")
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="refunds")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default="EGP")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reference = models.CharField(max_length=120, unique=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(amount__gt=0), name="refund_amount_positive")]


OrderStatus = Order.Status
PaymentStatus = Payment.Status
PaymentMethod = Payment.Method
