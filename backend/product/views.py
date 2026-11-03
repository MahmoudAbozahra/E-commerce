from django.db.models import Avg, Count, Exists, Min, OuterRef, Q
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from account.models import AuditLog
from order.models import Order, OrderItem

from .models import Brand, Category, Product, ProductImage, ProductVariant, Review, WishlistItem
from .serializers import (
    BrandSerializer,
    CategorySerializer,
    InventoryAdjustmentSerializer,
    InventoryMovementSerializer,
    ProductDetailSerializer,
    ProductImageSerializer,
    ProductListSerializer,
    ProductWriteSerializer,
    ReviewSerializer,
    VariantWriteSerializer,
    WishlistSerializer,
)
from .services import adjust_inventory


class CatalogProductViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    lookup_field = "slug"
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("name", "description", "variants__sku")
    ordering_fields = ("created_at", "name", "min_price")
    ordering = ("-created_at",)

    def get_queryset(self):
        qs = Product.objects.filter(status=Product.Status.ACTIVE).select_related("brand", "category").prefetch_related("variants", "images")
        qs = qs.annotate(
            min_price=Min("variants__price", filter=Q(variants__is_active=True)),
            available=Exists(ProductVariant.objects.filter(product=OuterRef("pk"), is_active=True, stock__gt=0)),
            rating_average=Avg("reviews__rating", filter=Q(reviews__is_approved=True)),
            review_count=Count("reviews", filter=Q(reviews__is_approved=True), distinct=True),
        )
        params = self.request.query_params
        if params.get("category"):
            qs = qs.filter(category__slug=params["category"])
        if params.get("brand"):
            qs = qs.filter(brand__slug=params["brand"])
        if params.get("min_price"):
            qs = qs.filter(variants__price__gte=params["min_price"])
        if params.get("max_price"):
            qs = qs.filter(variants__price__lte=params["max_price"])
        if params.get("available") in {"true", "1"}:
            qs = qs.filter(available=True)
        return qs.distinct()

    def get_serializer_class(self):
        return ProductDetailSerializer if self.action == "retrieve" else ProductListSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    serializer_class = CategorySerializer
    queryset = Category.objects.filter(is_active=True).select_related("parent")


class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    serializer_class = BrandSerializer
    queryset = Brand.objects.filter(is_active=True)


class StaffCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = CategorySerializer
    queryset = Category.objects.all()


class StaffBrandViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = BrandSerializer
    queryset = Brand.objects.all()


class StaffProductViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = ProductWriteSerializer
    queryset = Product.objects.all()


class StaffVariantViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = VariantWriteSerializer
    queryset = ProductVariant.objects.select_related("product")

    @action(detail=True, methods=("post",))
    def adjust_stock(self, request, pk=None):
        serializer = InventoryAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movement = adjust_inventory(variant=self.get_object(), actor=request.user, **serializer.validated_data)
        return Response(InventoryMovementSerializer(movement).data)


class StaffProductImageViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = ProductImageSerializer
    queryset = ProductImage.objects.select_related("product")


class WishlistViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = WishlistSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return WishlistItem.objects.none()
        return (
            WishlistItem.objects.filter(user=self.request.user)
            .select_related("product__brand", "product__category")
            .annotate(
                min_price=Min("product__variants__price"),
                available=Exists(ProductVariant.objects.filter(product=OuterRef("product_id"), stock__gt=0, is_active=True)),
                rating_average=Avg("product__reviews__rating", filter=Q(product__reviews__is_approved=True)),
                review_count=Count("product__reviews", filter=Q(product__reviews__is_approved=True)),
            )
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProductReviewViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [AllowAny()]
        if self.action == "moderate":
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_product(self):
        return Product.objects.get(pk=self.kwargs["product_pk"], status=Product.Status.ACTIVE)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Review.objects.none()
        if self.request.user.is_staff:
            return Review.objects.filter(product_id=self.kwargs["product_pk"])
        queryset = Review.objects.filter(product_id=self.kwargs["product_pk"]).order_by("-created_at")
        if self.action in {"list", "retrieve"}:
            owner = Q(user=self.request.user) if self.request.user.is_authenticated else Q(pk__isnull=True)
            return queryset.filter(Q(is_approved=True) | owner)
        return queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        product = self.get_product()
        verified = OrderItem.objects.filter(order__user=self.request.user, order__status=Order.Status.DELIVERED, variant__product=product).exists()
        if not verified:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("A delivered purchase is required to review this product.")
        serializer.save(user=self.request.user, product=product)

    def perform_update(self, serializer):
        serializer.save(is_approved=False)

    @action(detail=True, methods=("post",), permission_classes=(IsAdminUser,))
    def moderate(self, request, **kwargs):
        review = self.get_object()
        review.is_approved = bool(request.data.get("is_approved"))
        review.save(update_fields=("is_approved",))
        AuditLog.objects.create(
            actor=request.user, action="review.moderate", entity_type="review", entity_id=str(review.pk), details={"approved": review.is_approved}
        )
        return Response(self.get_serializer(review).data)
