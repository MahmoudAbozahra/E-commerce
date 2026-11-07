import hashlib
import html
import json
import re
import time
from datetime import date
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageOps

from product.management.demo_fashion.catalog import FASHION_PRODUCTS

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "AtelierCairoDemoAssetImporter/1.0 (development fixture; Wikimedia Commons attribution retained)"
ALLOWED_LICENSE_MARKERS = ("CC0", "CC BY", "Public domain", "No restrictions")
ASSET_ROOT = Path(__file__).resolve().parents[1] / "demo_fashion"
ASSET_DIR = ASSET_ROOT / "assets"
PROVENANCE_PATH = ASSET_ROOT / "ASSET_PROVENANCE.json"


def plain_text(value):
    return html.unescape(re.sub(r"<[^>]+>", " ", value or "")).replace("  ", " ").strip()


def request_json(url):
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=45) as response:
        return json.load(response)


def request_bytes(url):
    last_error = None
    for attempt in range(5):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "image/*"})
            with urlopen(request, timeout=60) as response:
                return response.read()
        except HTTPError as error:  # pragma: no cover - network retry path
            last_error = error
            retry_after = int(error.headers.get("Retry-After", 0) or 0)
            time.sleep(min(20, max(retry_after, 2 ** attempt * 2)))
        except Exception as error:  # pragma: no cover - network retry path
            last_error = error
            time.sleep(min(15, 2 ** attempt * 2))
    raise CommandError(f"Could not download {url}: {last_error}")


class Command(BaseCommand):
    help = "Fetch the pinned, reusable Wikimedia fashion photographs and record their provenance."

    def add_arguments(self, parser):
        parser.add_argument(
            "--accept-licenses",
            action="store_true",
            help="Confirm that the operator reviewed the recorded Commons licenses and attribution requirements.",
        )
        parser.add_argument("--refresh", action="store_true", help="Redownload and rebuild already present WebP assets.")

    def handle(self, *args, **options):
        if not options["accept_licenses"]:
            raise CommandError("Refusing to download assets without --accept-licenses. Review DEMO_FASHION_DATA.md first.")

        sources = tuple(dict.fromkeys(source for product in FASHION_PRODUCTS for source in product["sources"]))
        metadata = self._fetch_metadata(sources)
        missing = sorted(set(sources) - set(metadata))
        if missing:
            raise CommandError(f"Wikimedia did not return pinned files: {', '.join(missing)}")

        ASSET_DIR.mkdir(parents=True, exist_ok=True)
        previous_sources = {}
        if PROVENANCE_PATH.exists():
            previous_sources = {
                record["filename"]: record["source_title"]
                for record in json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
            }
        records = []
        for product in FASHION_PRODUCTS:
            for index, source_title in enumerate(product["sources"], start=1):
                info = metadata[source_title]
                ext = info.get("extmetadata", {})
                license_name = ext.get("LicenseShortName", {}).get("value", "")
                if not any(marker in license_name for marker in ALLOWED_LICENSE_MARKERS):
                    raise CommandError(f"Unsupported or unverifiable license {license_name!r} for {source_title}")

                filename = f"{product['slug']}-{index:02}.webp"
                asset_path = ASSET_DIR / filename
                if options["refresh"] or not asset_path.exists() or previous_sources.get(filename) != source_title:
                    source_filename = source_title.removeprefix("File:")
                    source_width = int(info["width"])
                    thumbnail_width = max(width for width in (120, 250, 330, 500, 960, 1280) if width < source_width)
                    thumbnail_url = f"https://commons.wikimedia.org/wiki/Special:Redirect/file/{quote(source_filename)}?width={thumbnail_width}"
                    payload = request_bytes(thumbnail_url)
                    self._write_webp(payload, asset_path)
                    time.sleep(0.4)

                payload = asset_path.read_bytes()
                with Image.open(asset_path) as image:
                    width, height = image.size
                records.append(
                    {
                        "filename": filename,
                        "product_slug": product["slug"],
                        "position": index,
                        "source_title": source_title,
                        "source_page": info.get("descriptionurl"),
                        "original_file_url": info.get("url"),
                        "creator": plain_text(ext.get("Artist", {}).get("value")),
                        "credit": plain_text(ext.get("Credit", {}).get("value")),
                        "license": license_name,
                        "license_url": ext.get("LicenseUrl", {}).get("value"),
                        "usage_terms": plain_text(ext.get("UsageTerms", {}).get("value")),
                        "retrieved_on": date.today().isoformat(),
                        "width": width,
                        "height": height,
                        "sha256": hashlib.sha256(payload).hexdigest(),
                        "asset_kind": "licensed photograph for development demo; not actual sellable inventory",
                    }
                )
                self.stdout.write(f"ready {filename}")

        PROVENANCE_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Prepared {len(records)} local WebP files with provenance at {PROVENANCE_PATH}."))

    @staticmethod
    def _fetch_metadata(titles):
        result = {}
        for offset in range(0, len(titles), 40):
            params = {
                "action": "query",
                "titles": "|".join(titles[offset : offset + 40]),
                "prop": "imageinfo",
                "iiprop": "url|size|mime|extmetadata",
                "iiurlwidth": 900,
                "format": "json",
                "formatversion": 2,
                "origin": "*",
            }
            data = request_json(f"{COMMONS_API}?{urlencode(params)}")
            for page in data.get("query", {}).get("pages", []):
                if page.get("missing") or not page.get("imageinfo"):
                    continue
                result[page["title"]] = page["imageinfo"][0]
        return result

    @staticmethod
    def _write_webp(payload, target):
        with Image.open(BytesIO(payload)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.thumbnail((1000, 1180), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (1000, 1250), "#eee8de")
            left = (canvas.width - image.width) // 2
            top = (canvas.height - image.height) // 2
            canvas.paste(image, (left, top))
            canvas.save(target, "WEBP", quality=84, method=6)
