from django.contrib import admin

from .models import Brand, Category, InventoryMovement, Product, ProductImage, ProductVariant, Review


class VariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


class ImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "brand", "category", "updated_at")
    list_filter = ("status", "brand", "category")
    search_fields = ("name", "slug", "variants__sku")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (VariantInline, ImageInline)


admin.site.register((Brand, Category, InventoryMovement, Review))
