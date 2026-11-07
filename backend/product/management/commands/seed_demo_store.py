from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from order.models import Coupon, ShippingMethod, ShippingZone
from product.demo_seed import DemoFashionSeeder, assert_demo_seed_allowed
from product.models import Brand, Category, InventoryMovement, Product, ProductVariant


class Command(BaseCommand):
    help = "Idempotently create development-only demo catalog, persistent media, shipping, stock, and coupon data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--deactivate-fashion-demo",
            action="store_true",
            help="Archive only the tagged fashion demo products without deleting records, orders, users, or media.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        assert_demo_seed_allowed()
        fashion = DemoFashionSeeder()
        if options["deactivate_fashion_demo"]:
            count = fashion.deactivate()
            self.stdout.write(self.style.WARNING(f"Archived {count} tagged fashion demo products; no records or media were deleted."))
            return

        electronics, _ = Category.objects.get_or_create(slug="electronics", defaults={"name": "Electronics", "is_active": True})
        home, _ = Category.objects.get_or_create(slug="home", defaults={"name": "Home", "is_active": True})
        nile, _ = Brand.objects.get_or_create(slug="nile-tech", defaults={"name": "Nile Tech", "is_active": True})
        phone, _ = Product.objects.get_or_create(
            slug="cairo-phone",
            defaults={"name": "Cairo Phone", "description": "Demo smartphone", "brand": nile, "category": electronics, "status": Product.Status.ACTIVE},
        )
        lamp, _ = Product.objects.get_or_create(
            slug="alexandria-lamp",
            defaults={"name": "Alexandria Lamp", "description": "Demo home lamp", "brand": nile, "category": home, "status": Product.Status.ACTIVE},
        )
        variants = (
            (phone, "CAIRO-BLK-128", {"color": "black", "storage": "128GB"}, "12999.00", 20),
            (phone, "CAIRO-BLU-256", {"color": "blue", "storage": "256GB"}, "15999.00", 10),
            (lamp, "LAMP-DEFAULT", {}, "850.00", 30),
        )
        for product, sku, options, price, stock in variants:
            self._ensure_variant(product, sku, options, price, stock)

        fashion.run()
        zone, _ = ShippingZone.objects.update_or_create(name="Egypt", defaults={"countries": ["EG"], "is_active": True})
        ShippingMethod.objects.update_or_create(
            code="egypt-standard",
            defaults={
                "zone": zone,
                "name": "Egypt standard delivery",
                "flat_fee": Decimal("60.00"),
                "estimated_days_min": 2,
                "estimated_days_max": 5,
                "is_active": True,
            },
        )
        Coupon.objects.update_or_create(
            code="WELCOME10",
            defaults={
                "kind": Coupon.Kind.PERCENT,
                "value": Decimal("10"),
                "max_discount": Decimal("500"),
                "minimum_subtotal": Decimal("500"),
                "valid_from": timezone.now() - timezone.timedelta(days=1),
                "valid_to": timezone.now() + timezone.timedelta(days=365),
                "total_limit": 1000,
                "per_user_limit": 1,
                "is_active": True,
            },
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Demo store data is ready with 60 fashion products and persistent fixture media. No users or credentials were created."
            )
        )

    @staticmethod
    def _ensure_variant(product, sku, options, price, stock):
        variant, created = ProductVariant.objects.get_or_create(
            sku=sku,
            defaults={"product": product, "option_values": options, "price": Decimal(price), "stock": stock},
        )
        if created:
            InventoryMovement.objects.create(
                variant=variant,
                delta=stock,
                reason=InventoryMovement.Reason.INITIAL,
                reference="seed_demo_store",
            )
