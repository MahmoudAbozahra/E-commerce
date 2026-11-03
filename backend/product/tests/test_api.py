from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.exceptions import ValidationError as APIValidationError
from rest_framework.test import APIClient

from product.models import Brand, Category, InventoryMovement, Product, ProductVariant, WishlistItem
from product.services import adjust_inventory

User = get_user_model()


class CatalogTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Phones", slug="phones")
        self.brand = Brand.objects.create(name="Nile Tech", slug="nile-tech")
        self.product = Product.objects.create(
            name="Cairo Phone", slug="cairo-phone", description="Phone", category=self.category, brand=self.brand, status=Product.Status.ACTIVE
        )
        self.variant = ProductVariant.objects.create(product=self.product, sku="PHONE-BLK", option_values={"color": "black"}, price=Decimal("9999.95"), stock=2)

    def test_catalog_is_public_filterable_and_customer_cannot_mutate(self):
        response = APIClient().get("/api/v1/catalog/products/?category=phones&available=true")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        customer = User.objects.create_user("customer", password="A-very-strong-passphrase-2026")
        client = APIClient()
        client.force_authenticate(customer)
        self.assertEqual(client.post("/api/v1/admin/catalog/products/", {}, format="json").status_code, 403)

    def test_duplicate_variant_option_combination_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ProductVariant.objects.create(product=self.product, sku="PHONE-BLK-2", option_values={"color": "black"}, price=Decimal("1"))

    def test_category_cycle_is_rejected(self):
        child = Category.objects.create(name="Child", slug="child", parent=self.category)
        self.category.parent = child
        with self.assertRaises(ValidationError):
            self.category.full_clean()

    def test_negative_variant_price_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ProductVariant.objects.create(product=self.product, sku="NEGATIVE", option_values={"color": "red"}, price=Decimal("-0.01"))

    def test_inventory_adjustment_is_locked_and_audited(self):
        staff = User.objects.create_user("stock-staff", email="stock@example.com", password="A-very-strong-passphrase-2026", is_staff=True)
        movement = adjust_inventory(variant=self.variant, delta=3, actor=staff, reason="delivery")
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 5)
        self.assertEqual(movement.reason, InventoryMovement.Reason.ADJUST)
        with self.assertRaises(APIValidationError):
            adjust_inventory(variant=self.variant, delta=-6, actor=staff, reason="invalid")

    def test_wishlist_is_unique_and_owner_scoped(self):
        user = User.objects.create_user("wishlist-user", email="wish@example.com", password="A-very-strong-passphrase-2026")
        item = WishlistItem.objects.create(user=user, product=self.product)
        with self.assertRaises(IntegrityError), transaction.atomic():
            WishlistItem.objects.create(user=user, product=self.product)
        client = APIClient()
        client.force_authenticate(user)
        self.assertEqual(client.get("/api/v1/wishlist/").data["count"], 1)
        other = User.objects.create_user("other-wishlist", email="other-wish@example.com", password="A-very-strong-passphrase-2026")
        client.force_authenticate(other)
        self.assertEqual(client.get(f"/api/v1/wishlist/{item.pk}/").status_code, 404)
