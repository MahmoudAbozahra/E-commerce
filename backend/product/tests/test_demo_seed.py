import mimetypes
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.parse import urlparse
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from product.management.demo_fashion.catalog import CATEGORY_GROUPS, DEMO_PRODUCT_SLUGS, FASHION_PRODUCTS
from product.models import Brand, Category, Product, ProductImage, ProductVariant


class DemoFashionSeedTests(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.media.name, DEBUG=True)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.addCleanup(self.media.cleanup)

    def test_seed_is_large_idempotent_persistent_and_preserves_unrelated_products(self):
        category = Category.objects.create(name="Original phones", slug="electronics")
        brand = Brand.objects.create(name="Original Nile", slug="nile-tech")
        original = Product.objects.create(
            name="Do not rewrite me",
            slug="cairo-phone",
            description="Existing content",
            category=category,
            brand=brand,
            status=Product.Status.DRAFT,
        )
        call_command("seed_demo_store", verbosity=0)
        counts_after_first = self._counts()
        call_command("seed_demo_store", verbosity=0)

        self.assertEqual(counts_after_first, self._counts())
        expected_images = sum(len(product["sources"]) for product in FASHION_PRODUCTS)
        self.assertEqual(counts_after_first, (60, 240, expected_images))
        self.assertGreaterEqual(Category.objects.filter(slug__in=[group["slug"] for group in CATEGORY_GROUPS]).count(), 10)
        original.refresh_from_db()
        self.assertEqual(original.name, "Do not rewrite me")
        self.assertEqual(original.description, "Existing content")
        self.assertEqual(original.status, Product.Status.DRAFT)

        products = Product.objects.filter(slug__in=DEMO_PRODUCT_SLUGS).prefetch_related("images")
        self.assertEqual(products.count(), len(FASHION_PRODUCTS))
        self.assertEqual(ProductImage.objects.filter(product__in=products).values("product_id", "image").distinct().count(), expected_images)
        for product in products:
            primary = next((image for image in product.images.all() if image.is_primary), None)
            self.assertIsNotNone(primary, product.slug)
            path = Path(self.media.name, primary.image.name)
            self.assertTrue(path.is_file(), path)
            with Image.open(path) as image:
                image.verify()

        call_command("validate_demo_fashion_media", verbosity=0)
        response = APIClient().get("/api/v1/catalog/products/?category=apparel&page_size=100")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 60)
        first_image = response.data["results"][0]["primary_image"]["url"]
        self.assertEqual(urlparse(first_image).path.rsplit(".", 1)[-1], "webp")
        self.assertEqual(mimetypes.guess_type(first_image)[0], "image/webp")

    def test_seed_refuses_production(self):
        with patch.dict(os.environ, {"DJANGO_ENVIRONMENT": "production"}), self.assertRaises(CommandError):
            call_command("seed_demo_store", verbosity=0)

    def test_media_repair_restores_files_without_changing_database_rows(self):
        call_command("seed_demo_store", verbosity=0)
        image = ProductImage.objects.filter(product__slug="ivory-blazer-set").order_by("sort_order").first()
        self.assertIsNotNone(image)
        image_count = ProductImage.objects.count()
        image_path = Path(self.media.name, image.image.name)
        image_path.unlink()

        call_command("repair_demo_fashion_media", verbosity=0)

        self.assertTrue(image_path.is_file())
        self.assertEqual(ProductImage.objects.count(), image_count)
        image.refresh_from_db()
        self.assertEqual(image.image.name, "demo-fashion/ivory-blazer-set/ivory-blazer-set-01.webp")

    @staticmethod
    def _counts():
        products = Product.objects.filter(slug__in=DEMO_PRODUCT_SLUGS)
        return (
            products.count(),
            ProductVariant.objects.filter(product__in=products).count(),
            ProductImage.objects.filter(product__in=products).count(),
        )

