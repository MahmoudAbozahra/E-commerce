from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from product.demo_seed import ASSET_DIR
from product.management.demo_fashion.catalog import FASHION_PRODUCTS
from product.models import Product


class Command(BaseCommand):
    help = "Restore missing demo-fashion media files for existing database image references without changing database rows."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report missing files without writing them.")

    def handle(self, *args, **options):
        restored = 0
        already_present = 0
        missing_products = []
        missing_references = []

        for item in FASHION_PRODUCTS:
            product = Product.objects.filter(slug=item["slug"]).only("id", "slug").first()
            if product is None:
                missing_products.append(item["slug"])
                continue

            referenced_names = set(product.images.values_list("image", flat=True))
            for index, _source in enumerate(item["sources"], start=1):
                filename = f"{item['slug']}-{index:02}.webp"
                storage_name = f"demo-fashion/{item['slug']}/{filename}"
                if storage_name not in referenced_names:
                    missing_references.append(storage_name)
                    continue
                if default_storage.exists(storage_name):
                    already_present += 1
                    continue

                fixture_path = ASSET_DIR / filename
                if not fixture_path.is_file():
                    raise CommandError(f"Missing pinned fixture asset: {fixture_path}")
                if not options["dry_run"]:
                    saved_name = default_storage.save(storage_name, ContentFile(fixture_path.read_bytes()))
                    if saved_name != storage_name:
                        raise CommandError(f"Storage changed deterministic demo path {storage_name!r} to {saved_name!r}")
                restored += 1

        action = "Would restore" if options["dry_run"] else "Restored"
        self.stdout.write(self.style.SUCCESS(f"{action} {restored} media files; {already_present} were already present. Database rows were not changed."))
        if missing_products:
            self.stdout.write(self.style.WARNING(f"Skipped {len(missing_products)} demo products absent from the database."))
        if missing_references:
            self.stdout.write(self.style.WARNING(f"Skipped {len(missing_references)} files with no matching ProductImage row."))
