from django.contrib import admin

from .models import (
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


class ItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "sku", "option_values", "unit_price", "quantity", "line_total")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("reference", "user", "status", "total", "currency", "created_at")
    list_filter = ("status", "currency")
    search_fields = ("reference", "user__username", "user__email")
    readonly_fields = (
        "reference",
        "subtotal",
        "coupon_discount",
        "points_discount",
        "shipping_fee",
        "tax",
        "total",
        "shipping_address",
        "created_at",
        "updated_at",
    )
    inlines = (ItemInline,)


admin.site.register(
    (Coupon, ShippingZone, ShippingMethod, Payment, Refund, ReturnRequest, ReturnStatusHistory, LoyaltyWallet, LoyaltyTransaction, OrderStatusHistory)
)
