import os
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import CommandError

from product.management.demo_fashion.catalog import (
    CATEGORY_GROUPS,
    DEMO_BRAND_SLUG,
    DEMO_PRODUCT_SLUGS,
    DEMO_ROOT_CATEGORY_SLUG,
    FASHION_PRODUCTS,
)
from product.models import Brand, Category, InventoryMovement, Product, ProductImage, ProductVariant

ASSET_DIR = Path(__file__).resolve().parent / "management" / "demo_fashion" / "assets"


def assert_demo_seed_allowed():
    environment = os.environ.get("DJANGO_ENVIRONMENT", "development").strip().lower()
    if environment == "production" or (not settings.DEBUG and environment != "staging"):
        raise CommandError("Refusing to seed demo inventory outside DEBUG development/test or an explicitly named staging environment.")


class DemoFashionSeeder:
    def deactivate(self):
        return Product.objects.filter(slug__in=DEMO_PRODUCT_SLUGS).update(status=Product.Status.ARCHIVED, featured=False)

    def run(self):
        if not ASSET_DIR.exists():
            raise CommandError("Fashion fixture assets are missing. Run `python manage.py fetch_demo_fashion_assets --accept-licenses` first.")
        root, _ = Category.objects.update_or_create(
            slug=DEMO_ROOT_CATEGORY_SLUG,
            defaults={
                "name": "Fashion",
                "description": "Development-only fashion catalogue. Photography is illustrative, licensed demo media—not actual sellable inventory.",
                "is_active": True,
                "sort_order": 1,
                "parent": None,
            },
        )
        category_map = {}
        for order, group in enumerate(CATEGORY_GROUPS, start=1):
            category, _ = Category.objects.update_or_create(
                slug=group["slug"],
                defaults={
                    "name": group["name"],
                    "description": group["description"],
                    "parent": root,
                    "is_active": True,
                    "sort_order": order,
                },
            )
            category_map[group["slug"]] = category

        brand, _ = Brand.objects.update_or_create(
            slug=DEMO_BRAND_SLUG,
            defaults={
                "name": "Atelier Cairo",
                "description": "Fictional development brand. Demo photography is credited separately and does not depict actual inventory for sale.",
                "is_active": True,
            },
        )
        for item in FASHION_PRODUCTS:
            product, _ = Product.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "name": item["name"],
                    "description": (
                        f"{item['name']} is a development-only {category_map[item['category_slug']].name.lower()} piece in a {item['color']} palette. "
                        "The photograph is reusable illustrative demo media and is not a claim that this exact item is available for commercial sale."
                    ),
                    "brand": brand,
                    "category": category_map[item["category_slug"]],
                    "status": Product.Status.ACTIVE,
                    "featured": item["featured"],
                },
            )
            stock_pattern = self._stock_pattern(item["availability"])
            for index, size in enumerate(item["sizes"]):
                self._ensure_variant(
                    product,
                    f"{item['slug'].upper()}-{size}",
                    {"color": item["color"], "size": size},
                    item["price"],
                    stock_pattern[index],
                )
            self._sync_images(product, item)

    @staticmethod
    def _stock_pattern(availability):
        if availability == "out":
            return (0, 0, 0, 0)
        if availability == "limited":
            return (0, 1, 2, 0)
        return (6, 10, 12, 7)

    @staticmethod
    def _ensure_variant(product, sku, options, price, stock):
        variant, created = ProductVariant.objects.get_or_create(
            sku=sku,
            defaults={
                "product": product,
                "option_values": options,
                "price": Decimal(price),
                "stock": stock,
                "low_stock_threshold": 3,
                "is_active": True,
            },
        )
        if created:
            if stock:
                InventoryMovement.objects.create(
                    variant=variant,
                    delta=stock,
                    reason=InventoryMovement.Reason.INITIAL,
                    reference="seed_demo_store",
                )
            return
        variant.product = product
        variant.option_values = options
        variant.price = Decimal(price)
        variant.low_stock_threshold = 3
        variant.is_active = True
        variant.save()

    @staticmethod
    def _sync_images(product, item):
        for index, _source_title in enumerate(item["sources"], start=1):
            filename = f"{item['slug']}-{index:02}.webp"
            fixture_path = ASSET_DIR / filename
            if not fixture_path.exists():
                raise CommandError(f"Missing pinned fashion asset: {fixture_path}")
            storage_name = f"demo-fashion/{item['slug']}/{filename}"
            if not default_storage.exists(storage_name):
                saved_name = default_storage.save(storage_name, ContentFile(fixture_path.read_bytes()))
                if saved_name != storage_name:
                    raise CommandError(f"Storage changed deterministic demo path {storage_name!r} to {saved_name!r}")

            alt_text = f"{item['name']} — {'primary' if index == 1 else f'alternate {index}'} fashion view"
            record = product.images.filter(image=storage_name).first()
            if index == 1:
                current_primary = product.images.filter(is_primary=True).first()
                if record is None:
                    record = current_primary or ProductImage(product=product)
                if current_primary and current_primary.pk != record.pk:
                    current_primary.is_primary = False
                    current_primary.save(update_fields=("is_primary",))
                record.image.name = storage_name
                record.alt_text = alt_text
                record.sort_order = 0
                record.is_primary = True
                record.save()
            else:
                if record is None:
                    record = ProductImage(product=product, image=storage_name)
                record.alt_text = alt_text
                record.sort_order = index - 1
                record.is_primary = False
                record.save()
