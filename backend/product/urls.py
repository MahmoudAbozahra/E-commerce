from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BrandViewSet,
    CatalogProductViewSet,
    CategoryViewSet,
    ProductReviewViewSet,
    StaffBrandViewSet,
    StaffCategoryViewSet,
    StaffProductImageViewSet,
    StaffProductViewSet,
    StaffVariantViewSet,
    WishlistViewSet,
)

public = DefaultRouter()
public.register("catalog/categories", CategoryViewSet, basename="category")
public.register("catalog/brands", BrandViewSet, basename="brand")
public.register("catalog/products", CatalogProductViewSet, basename="product")
public.register("wishlist", WishlistViewSet, basename="wishlist")
staff = DefaultRouter()
staff.register("admin/catalog/categories", StaffCategoryViewSet, basename="admin-category")
staff.register("admin/catalog/brands", StaffBrandViewSet, basename="admin-brand")
staff.register("admin/catalog/products", StaffProductViewSet, basename="admin-product")
staff.register("admin/catalog/variants", StaffVariantViewSet, basename="admin-variant")
staff.register("admin/catalog/images", StaffProductImageViewSet, basename="admin-product-image")

review_list = ProductReviewViewSet.as_view({"get": "list", "post": "create"})
review_detail = ProductReviewViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"})
review_moderate = ProductReviewViewSet.as_view({"post": "moderate"})

urlpatterns = [
    path("", include(public.urls)),
    path("", include(staff.urls)),
    path("catalog/products/<int:product_pk>/reviews/", review_list),
    path("catalog/products/<int:product_pk>/reviews/<int:pk>/", review_detail),
    path("catalog/products/<int:product_pk>/reviews/<int:pk>/moderate/", review_moderate),
]
