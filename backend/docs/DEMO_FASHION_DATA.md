# Development Fashion Demo Data
الـdataset ده للتطوير والـstaging فقط، ومش inventory حقيقي ولا عروض مسموح بفهرستها في production.
## الأرقام

- 60 fashion products مميزين.
- root category واحدة `apparel` باسم Fashion + 10 subcategories.
- 240 variants: أربع مقاسات/waists لكل منتج، مع available/limited/out-of-stock examples.
- 87 local WebP photographs؛ 60 primary images و27 gallery images إضافية.
- 12 products عليها `featured=True`؛ homepage rail بيختار أول 10 متاحين.
- 0 transparent cutouts؛ الـrail بيستخدم photo-card fallback موثق.

المنتجات القديمة غير المرتبطة بالديمو، زي electronics/home، لا يتم حذفها. الـseed يستخدم `get_or_create` للـbaseline records عشان ميكتبش فوق بيانات موجودة بنفس slugs.

## الملفات وحقوق الاستخدام

- Specs: `product/management/demo_fashion/catalog.py`
- Stable source fixtures: `product/management/demo_fashion/assets/*.webp`
- Provenance لكل ملف: `product/management/demo_fashion/ASSET_PROVENANCE.json`
- Downloader: `product/management/commands/fetch_demo_fashion_assets.py`
- Seeder/storage repair: `product/demo_seed.py` و`seed_demo_store.py`
- Files-only repair من غير أي database writes: `repair_demo_fashion_media.py`
- Validator: `validate_demo_fashion_media.py`

كل source مثبت باسم Wikimedia Commons file، ومعاه source page، creator/credit، license، license URL، retrieval date وSHA-256. الـlicenses مختلطة حسب الملف (CC0/Public Domain/CC BY/CC BY-SA). لازم الاحتفاظ بالـmanifest وتطبيق attribution/share-alike حسب كل record. المشروع لا يدّعي ملكية الصور، ولا يعتبرها تصوير منتجات Atelier Cairo فعلية.

الـfetch command لا يعمل من غير `--accept-licenses`، وبيستخدم Wikimedia standard thumbnail sizes لتجنب الضغط على originals. الصور محلية وقت التشغيل؛ مفيش hotlink dependency.

## Safe setup

استخدم DB وmedia منفصلين، واضبط `DJANGO_ENVIRONMENT=development` ثم:

```powershell
uv run python manage.py migrate
uv run python manage.py seed_demo_store
uv run python manage.py validate_demo_fashion_media
```

الـseed يرفض `DJANGO_ENVIRONMENT=production`، ويرفض `DEBUG=False` إلا لو البيئة مسماة `staging` صراحة. تشغيله مرتين لا يعمل duplicates ولا يعيد initial stock movements، ولا يغير users/orders.

لو DB row موجود لكن ملف storage ناقص، الـseed يعيد نسخ WebP إلى المسار الثابت:

```text
demo-fashion/<product-slug>/<product-slug>-01.webp
```

ده هو إصلاح dangling media references اللي كانت بتنتج 404 وصور مكسورة.

لو الـProductImage rows صحيحة ومش عايز تعمل أي تغيير في الـdatabase، استخدم الإصلاح الخاص بالملفات فقط:

```powershell
uv run python manage.py repair_demo_fashion_media --dry-run
uv run python manage.py repair_demo_fashion_media
uv run python manage.py validate_demo_fashion_media
```

الأمر بيقرأ الـrows الموجودة، وينسخ فقط الـWebP الناقص إلى المسار المشار له؛ لا يعمل `INSERT` أو `UPDATE` أو `DELETE`.

## تحديث أو تعطيل الديمو

إضافة منتج: أضفه إلى `catalog.py`، راجع مصدره وترخيصه، شغّل fetch ثم seed وvalidator. البيانات الحقيقية تتضاف من Django Admin/staff API، مش من fixture.

لتعطيل الديمو بأمان من غير delete:

```powershell
uv run python manage.py seed_demo_store --deactivate-fashion-demo
```

ده بيحوّل فقط الـ60 slugs المثبتين إلى `archived`، ومبيحذفش records أو media أو customer data. مفيش destructive cleanup command عمدًا.

في production استخدم object storage durable وCDN، وسيب `NEXT_PUBLIC_INDEX_SITE=false` لأي بيئة فيها الديمو.

