from django.db.models import Count, F, Sum

from product.models import ProductVariant

from .models import LoyaltyWallet, Order, Payment


def order_list_for_user(*, user, reference: str = "", status: str = ""):
    queryset = Order.objects.select_related("coupon", "shipping_method").prefetch_related("items", "payments")
    if not user.is_staff:
        queryset = queryset.filter(user=user)
    if reference:
        queryset = queryset.filter(reference__icontains=reference)
    if status:
        queryset = queryset.filter(status=status)
    return queryset


def commerce_report_summary() -> dict:
    paid = Order.objects.filter(payments__status=Payment.Status.PAID).exclude(status=Order.Status.CANCELLED).distinct()
    return {
        "recognized_revenue": paid.aggregate(value=Sum("total"))["value"] or 0,
        "orders_by_status": list(Order.objects.values("status").annotate(count=Count("id")).order_by("status")),
        "best_selling_variants": list(
            ProductVariant.objects.filter(order_items__order__in=paid).values("sku").annotate(quantity=Sum("order_items__quantity")).order_by("-quantity")[:20]
        ),
        "low_stock": list(ProductVariant.objects.filter(stock__lte=F("low_stock_threshold"), is_active=True).values("id", "sku", "stock")),
        "loyalty_liability_points": LoyaltyWallet.objects.aggregate(value=Sum("available_points"))["value"] or 0,
    }
