# دليل Architecture وتشغيل الـFrontend
## فين تعدّل كل حاجة؟
| المطلوب | الملف الأساسي |
|---|---|
| Homepage وترتيب sections | `src/app/(store)/page.tsx` |
| Header/navigation | `src/shared/ui/site-header.tsx` |
| Footer | `src/shared/ui/site-footer.tsx` |
| Circular clothing rail وQuick Preview motion | `src/features/showcase/product-rail.tsx` |
| Product card | `src/features/catalog/product-card.tsx` |
| الصورة/fallback | `src/features/catalog/product-media.tsx`, `src/shared/ui/resilient-image.tsx` |
| Product detail وSEO/JSON-LD | `src/app/(store)/products/[slug]/page.tsx` |
| Circular product gallery | `src/features/catalog/product-gallery.tsx` |
| Variant/cart/wishlist buttons | `src/features/commerce/purchase-panel.tsx` |
| Color/style/shape option orbit | `src/features/commerce/variant-option-orbit.tsx` |
| Catalog filters/pagination | `src/features/catalog/catalog-filters.tsx`, `pagination.tsx` |
| Cart | `src/features/cart/cart-view.tsx` |
| Checkout | `src/features/checkout/checkout-view.tsx` |
| Account/addresses | `src/features/auth/account-dashboard.tsx` |
| Login/register | `src/features/auth/auth-form.tsx` |
| Orders | `src/features/orders/` |
| Design tokens/global CSS | `src/app/globals.css` |

## ملكية البيانات

Django هو المصدر الوحيد للـproducts، slugs، categories، prices، variants، stock، image metadata، orders وusers. ممنوع إضافة array منتجات ثابتة في React؛ ده هيكسر SEO consistency والـcheckout authority. Next مسؤول عن rendering، navigation، interaction، caching وBFF cookies. الـrail بيستقبل products جاية من Django؛ الـcuration بتتحدد من حقل `featured` في backend seed/admin.

لإضافة field جديد: عدّل Django model/serializer مع migration لو مطلوب، حدّث `backend/schema.yml`، شغّل `npm run generate:api`، وبعدها استخدم generated type. لإضافة endpoint خاص: ضيفه في Django، وبعدين أضف prefix محدود في `src/app/api/backend/[...path]/route.ts` لو محتاج authenticated browser access.

## إضافة صفحة أو Component أو Test

- صفحة public: `src/app/(store)/اسم/page.tsx`؛ ضيف metadata/canonical وروابط اكتشاف.
- صفحة account: `src/app/(account)/اسم/page.tsx`؛ خلّي Django/BFF هو authority للصلاحية وأضف `noindex`.
- reusable UI: `src/shared/ui` لو generic، أو `src/features/<domain>` لو business-specific.
- unit/integration: جنب الملف باسم `*.test.ts(x)`.
- browser journey: `frontend/e2e/storefront.spec.ts`.
- Category جديدة أو product/variant/image: Django admin للبيانات الحقيقية، أو `product/management/demo_fashion/catalog.py` للديمو فقط.

## Image pipeline بعد الإصلاح

```text
Repo fixture WebP
backend/product/management/demo_fashion/assets/*.webp
  -> seed_demo_store copies deterministic path
DJANGO_MEDIA_ROOT/demo-fashion/<slug>/<file>.webp
  -> ProductImage.image
  -> ProductListSerializer.primary_image / ProductDetailSerializer.images
  -> URL مثل http://127.0.0.1:8000/media/demo-fashion/...
  -> mediaUrl() يحوله /media/demo-fashion/...
  -> Next rewrite يproxy إلى DJANGO_API_URL في local dev
  -> next/image optimizer
  -> browser img naturalWidth > 0
```

الـroot cause القديم كان DB rows موجودة والملفات نفسها اتحذفت، والـseed كان بيعمل return لمجرد وجود row. الـseed الجديد يراجع `default_storage.exists()` ويعيد نسخ fixture لو object ناقص. Django بيسجل MIME `image/webp` صراحة على Windows. `ResilientImage` fallback لحالات فردية فعلية، مش لإخفاء seed مكسور.

في production: استخدم durable S3/R2-compatible storage مع CDN. خلي `ProductImage.image.url` public HTTPS، واضبط `NEXT_PUBLIC_MEDIA_ORIGIN=https://cdn.example.com`. `next.config.ts` بيضيف الـorigin لـremote patterns. متستخدمش local filesystem في multi-instance production.

## تشغيل clean isolated development setup على PowerShell

الأوامر دي بتنشئ DB/media منفصلين ومش بتلمس `backend/db.sqlite3`:

```powershell
cd D:\my_work\Projects\Ecommerce-API\backend
$devRoot = Join-Path $env:LOCALAPPDATA "AtelierCairoDev"
New-Item -ItemType Directory -Path $devRoot -Force | Out-Null
$env:DJANGO_ENVIRONMENT = "development"
$env:DB_ENGINE = "django.db.backends.sqlite3"
$env:DB_NAME = Join-Path $devRoot "fashion.sqlite3"
$env:DJANGO_MEDIA_ROOT = Join-Path $devRoot "media"
uv sync
uv run python manage.py migrate
uv run python manage.py seed_demo_store
uv run python manage.py validate_demo_fashion_media
uv run python manage.py runserver 127.0.0.1:8000
```

الصور الـ87 موجودة أصلًا في repo fixtures. لإعادة استيرادها من Wikimedia فقط بعد مراجعة licenses:

```powershell
uv run python manage.py fetch_demo_fashion_assets --accept-licenses
```

الـcommand بيرفض production. لإخفاء الديمو من storefront من غير حذف orders/users/media:

```powershell
uv run python manage.py seed_demo_store --deactivate-fashion-demo
```

Frontend في terminal تاني:

```powershell
cd D:\my_work\Projects\Ecommerce-API\frontend
Copy-Item .env.example .env.local
# DJANGO_API_URL=http://127.0.0.1:8000
# NEXT_PUBLIC_MEDIA_ORIGIN=       # فاضي في local: same-origin /media rewrite
# NEXT_PUBLIC_SITE_URL=http://localhost:3000
# NEXT_PUBLIC_INDEX_SITE=false
npm ci
npm run dev
```

`NEXT_PUBLIC_INDEX_SITE=false` مهم لأي demo/staging. المنتجات الديمو مش inventory حقيقي ومينفعش تتفهرس كعروض تجارية.

## إضافة منتج ديمو واحد

1. أضف record داخل group مناسب في `backend/product/management/demo_fashion/catalog.py` مع slug ثابت وsource title حقيقي من Wikimedia.
2. راجع license/source، ثم شغّل `fetch_demo_fashion_assets --accept-licenses`؛ الـprovenance يتحدث تلقائيًا.
3. شغّل `seed_demo_store` على DB تطوير معزولة.
4. شغّل `validate_demo_fashion_media`، backend tests، generated schema وfrontend tests.
5. متحطش السعر أو SKU أو stock في React.

للمنتج الحقيقي استخدم Django Admin أو staff API وارفع media إلى storage الإنتاجي؛ متعدّلوش fixture catalog.

## أوامر التحقق

```powershell
# backend
cd backend
uv run ruff check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python -m pytest
uv run python manage.py validate_demo_fashion_media
uv run python manage.py spectacular --file schema.yml --validate

# frontend
cd ..\frontend
npm run generate:api
npm run typecheck
npm run lint
npm run test:run
npm run build
npm run test:e2e
```

Playwright بيتحقق من `naturalWidth > 0`، عدم ظهور `[data-image-fallback]`، وعدم وجود failed `/media` أو `/_next/image` responses على desktop/mobile/reduced-motion.

## الأداء وSEO

- homepage circular rail بيحمّل الصور القريبة من مركز الـorbit كـpriority؛ باقي الصور lazy.
- cards تستخدم responsive `sizes` وNext optimizer؛ مفيش 60 eager image.
- كل product page SSR/direct reload وOG image/JSON-LD بتستخدم absolute public URL.
- filtered catalog URLs غير مفهرسة لتجنب duplicate content.
- sitemap بيقرأ كل صفحات pagination من Django.
- الديمو/staging يفضل `robots: disallow` لحد استبدال fixtures بinventory حقيقي.

## حدود حالية معلنة

- الـrail بيستخدم 10 صور حقيقية على circular 3D orbit: الصورة النشطة في المقدمة، والجوانب أصغر وأبعد بصريًا، مع cyclic wrap وdrag/swipe وأسهم. عدد transparent cutouts الحالي **صفر**؛ الصور المعروضة مرخّصة ومثبت مصدرها بدل ادعاء alpha cutout غير متاح.
- 60 منتج، 87 صورة: كل منتج له primary؛ 27 صور gallery إضافية لقطع لها زوايا مناسبة. مش كل منتج له 2–4 زوايا لأننا رفضنا ربط صور غير مطابقة لمجرد زيادة العدد.
- الصور licensed demo imagery ومش صور inventory حقيقي. Attribution/provenance في backend manifest.
- الدفع COD فقط؛ returns form وstaff frontend مش منفذين.

