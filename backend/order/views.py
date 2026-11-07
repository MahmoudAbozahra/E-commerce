from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from product.models import ProductImage, ProductVariant

from .models import Cart, CartItem, Coupon, LoyaltyTransaction, LoyaltyWallet, Order, Payment, Refund, ReturnRequest, ShippingMethod, ShippingZone
from .selectors import commerce_report_summary, order_list_for_user
from .serializers import (
    CartItemSerializer,
    CartSerializer,
    CheckoutRequestSerializer,
    CouponSerializer,
    CouponValidateSerializer,
    LoyaltyAdjustmentSerializer,
    LoyaltyTransactionSerializer,
    OrderSerializer,
    PaymentSerializer,
    QuoteRequestSerializer,
    RefundSerializer,
    ReturnDecisionSerializer,
    ReturnRequestSerializer,
    ReturnTimelineSerializer,
    ShippingMethodSerializer,
    ShippingZoneSerializer,
    TimelineSerializer,
    TransitionSerializer,
    WalletSerializer,
)
from .services import adjust_loyalty, calculate_quote, checkout, collect_cod, complete_refund, create_return_request, decide_return, transition_order

User = get_user_model()


class HealthView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(responses={200: {"type": "object", "properties": {"status": {"type": "string"}}}})
    def get(self, request):
        return Response({"status": "ok"})


class CartView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_cart(self, user):
        cart, _ = Cart.objects.get_or_create(user=user)
        return Cart.objects.prefetch_related(
            "items__variant__product",
            Prefetch("items__variant__product__images", queryset=ProductImage.objects.order_by("sort_order", "id"), to_attr="catalog_images"),
        ).get(pk=cart.pk)

    @extend_schema(responses=CartSerializer)
    def get(self, request):
        return Response(CartSerializer(self.get_cart(request.user)).data)

    @extend_schema(responses={204: None})
    @transaction.atomic
    def delete(self, request):
        cart = Cart.objects.select_for_update().filter(user=request.user).first()
        if cart:
            cart.items.all().delete()
        return Response(status=204)


class CartItemViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = CartItemSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CartItem.objects.none()
        return (
            CartItem.objects.filter(cart__user=self.request.user)
            .select_related("variant__product")
            .prefetch_related(Prefetch("variant__product__images", queryset=ProductImage.objects.order_by("sort_order", "id"), to_attr="catalog_images"))
        )

    @transaction.atomic
    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        cart = Cart.objects.select_for_update().get(pk=cart.pk)
        variant = ProductVariant.objects.select_for_update().get(pk=serializer.validated_data["variant"].pk)
        existing = cart.items.filter(variant=variant).first()
        if existing:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"variant_id": "Variant already exists in cart; update that item."})
        serializer.save(cart=cart, variant=variant)


class ShippingMethodList(generics.ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ShippingMethodSerializer
    queryset = ShippingMethod.objects.filter(is_active=True, zone__is_active=True).select_related("zone").order_by("name", "id")


class StaffShippingZoneViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = ShippingZoneSerializer
    queryset = ShippingZone.objects.all()


class StaffShippingMethodViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = ShippingMethodSerializer
    queryset = ShippingMethod.objects.select_related("zone")


class StaffCouponViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = CouponSerializer
    queryset = Coupon.objects.prefetch_related("products", "categories")


class QuoteView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=QuoteRequestSerializer, responses={200: dict})
    def post(self, request):
        serializer = QuoteRequestSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        quote = calculate_quote(
            user=request.user,
            address=data["address"],
            shipping_method_id=data["shipping_method"].pk,
            coupon_code=data["coupon_code"],
            points=data["points"],
        )
        return Response(
            {key: value for key, value in quote.items() if key not in {"lines", "shipping", "coupon", "wallet"}}
            | {"disclaimer": "A quote is not a price or stock guarantee; checkout recomputes all values."}
        )


class CheckoutView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=CheckoutRequestSerializer, responses={200: OrderSerializer, 201: OrderSerializer})
    def post(self, request):
        serializer = CheckoutRequestSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        order, created = checkout(
            user=request.user,
            address=data["address"],
            shipping_method_id=data["shipping_method"].pk,
            coupon_code=data["coupon_code"],
            points=data["points"],
            idempotency_key=request.headers.get("Idempotency-Key", ""),
        )
        return Response(OrderSerializer(order).data, status=201 if created else 200)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrderSerializer
    lookup_field = "pk"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        return order_list_for_user(
            user=self.request.user,
            reference=self.request.query_params.get("reference", ""),
            status=self.request.query_params.get("status", ""),
        )

    @action(detail=True, methods=("post",))
    def cancel(self, request, pk=None):
        order = self.get_object()
        order = transition_order(order=order, new_status=Order.Status.CANCELLED, actor=request.user, note="Customer cancellation")
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=("get",))
    def timeline(self, request, pk=None):
        return Response(TimelineSerializer(self.get_object().timeline.select_related("actor"), many=True).data)

    @action(detail=True, methods=("post",), permission_classes=(IsAdminUser,))
    def transition(self, request, pk=None):
        serializer = TransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = transition_order(
            order=self.get_object(), actor=request.user, new_status=serializer.validated_data["status"], note=serializer.validated_data.get("note", "")
        )
        return Response(self.get_serializer(order).data)


class CouponValidateView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=CouponValidateSerializer, responses={200: dict})
    def post(self, request):
        serializer = CouponValidateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        quote = calculate_quote(
            user=request.user,
            address=serializer.validated_data["address"],
            shipping_method_id=serializer.validated_data["shipping_method"].pk,
            coupon_code=serializer.validated_data["code"],
        )
        return Response({"valid": True, "discount": quote["coupon_discount"], "currency": "EGP"})


class WalletView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses=WalletSerializer)
    def get(self, request):
        wallet, _ = LoyaltyWallet.objects.get_or_create(user=request.user)
        return Response(WalletSerializer(wallet).data)


class LoyaltyTransactionList(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = LoyaltyTransactionSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return LoyaltyTransaction.objects.none()
        return LoyaltyTransaction.objects.filter(wallet__user=self.request.user)


class StaffPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = PaymentSerializer
    queryset = Payment.objects.select_related("order")

    @action(detail=True, methods=("post",))
    def collect(self, request, pk=None):
        return Response(self.get_serializer(collect_cod(payment=self.get_object(), actor=request.user)).data)


class ReturnViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = ReturnRequestSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ReturnRequest.objects.none()
        qs = ReturnRequest.objects.select_related("order_item__order")
        return qs if self.request.user.is_staff else qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.instance = create_return_request(user=self.request.user, **serializer.validated_data)

    @action(detail=True, methods=("get",))
    def timeline(self, request, pk=None):
        return Response(ReturnTimelineSerializer(self.get_object().timeline.select_related("actor"), many=True).data)

    @action(detail=True, methods=("post",), permission_classes=(IsAdminUser,))
    def decide(self, request, pk=None):
        serializer = ReturnDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        returned = decide_return(
            returned=self.get_object(),
            decision=serializer.validated_data["status"],
            actor=request.user,
            note=serializer.validated_data.get("staff_note", ""),
        )
        return Response(self.get_serializer(returned).data)


class RefundViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = RefundSerializer
    queryset = Refund.objects.select_related("return_request", "payment")

    @action(detail=True, methods=("post",))
    def complete(self, request, pk=None):
        return Response(self.get_serializer(complete_refund(refund=self.get_object(), actor=request.user)).data)


class LoyaltyAdjustmentView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(request=LoyaltyAdjustmentSerializer, responses={201: LoyaltyTransactionSerializer})
    def post(self, request):
        serializer = LoyaltyAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(pk=serializer.validated_data["user_id"])
        event = adjust_loyalty(
            user=user,
            delta=serializer.validated_data["delta"],
            actor=request.user,
            reason=serializer.validated_data["reason"],
        )
        return Response(LoyaltyTransactionSerializer(event).data, status=201)


class ReportsView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(responses={200: dict})
    def get(self, request):
        return Response(commerce_report_summary())
