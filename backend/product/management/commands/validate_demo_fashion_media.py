from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from PIL import Image

from product.management.demo_fashion.catalog import DEMO_PRODUCT_SLUGS
from product.models import Product


class Command(BaseCommand):
    help = "Validate that every tagged demo fashion image exists in storage and decodes as a real image."

    def handle(self, *args, **options):
        products = Product.objects.filter(slug__in=DEMO_PRODUCT_SLUGS).prefetch_related("images")
        failures = []
        image_count = 0
        primary_count = 0
        for product in products:
            images = list(product.images.all())
            if not any(image.is_primary for image in images):
                failures.append(f"{product.slug}: no primary image")
            for image in images:
                image_count += 1
                primary_count += int(image.is_primary)
                name = image.image.name
                if not name or not default_storage.exists(name):
                    failures.append(f"{product.slug}: missing storage object {name!r}")
                    continue
                try:
                    with default_storage.open(name, "rb") as source:
                        with Image.open(source) as decoded:
                            decoded.verify()
                except Exception as error:
                    failures.append(f"{product.slug}: unreadable {name!r}: {error}")
        if products.count() != len(DEMO_PRODUCT_SLUGS):
            failures.append(f"expected {len(DEMO_PRODUCT_SLUGS)} products, found {products.count()}")
        if failures:
            raise CommandError("\n".join(failures))
        self.stdout.write(
            self.style.SUCCESS(
                f"Validated {products.count()} demo fashion products, {image_count} readable images, and {primary_count} primary images."
            )
        )
