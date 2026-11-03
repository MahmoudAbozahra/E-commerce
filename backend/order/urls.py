from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CartItemViewSet,
    CartView,
    CheckoutView,
    CouponValidateView,
    HealthView,
    LoyaltyAdjustmentView,
    LoyaltyTransactionList,
    OrderViewSet,
    QuoteView,
    RefundViewSet,
    ReportsView,
    ReturnViewSet,
    ShippingMethodList,
    StaffCouponViewSet,
    StaffPaymentViewSet,
    StaffShippingMethodViewSet,
    StaffShippingZoneViewSet,
    WalletView,
)

router = DefaultRouter()
router.register("cart/items", CartItemViewSet, basename="cart-item")
router.register("orders/returns", ReturnViewSet, basename="return")
router.register("orders", OrderViewSet, basename="order")
router.register("admin/payments", StaffPaymentViewSet, basename="admin-payment")
router.register("admin/refunds", RefundViewSet, basename="admin-refund")
router.register("admin/coupons", StaffCouponViewSet, basename="admin-coupon")
router.register("admin/shipping/zones", StaffShippingZoneViewSet, basename="admin-shipping-zone")
router.register("admin/shipping/methods", StaffShippingMethodViewSet, basename="admin-shipping-method")

urlpatterns = [
    path("health/", HealthView.as_view()),
    path("cart/", CartView.as_view()),
    path("shipping/methods/", ShippingMethodList.as_view()),
    path("checkout/preview/", QuoteView.as_view()),
    path("checkout/", CheckoutView.as_view()),
    path("coupons/validate/", CouponValidateView.as_view()),
    path("loyalty/wallet/", WalletView.as_view()),
    path("loyalty/transactions/", LoyaltyTransactionList.as_view()),
    path("admin/loyalty/adjustments/", LoyaltyAdjustmentView.as_view()),
    path("admin/reports/summary/", ReportsView.as_view()),
    path("", include(router.urls)),
]
