# خريطة Routes الفعلية للـFrontend
الملف ده بيوصف الكود الموجود فعلًا تحت `frontend/src/app` بتاريخ المراجعة، مش routes مقترحة. المشروع بيستخدم Next.js App Router. الأقواس العادية زي `(store)` و`(account)` اسمها **Route Groups** لتنظيم الملفات فقط، ومش بتظهر في URL. الأقواس المربعة زي `[slug]` و`[id]` أجزاء Dynamic بتتبدل بقيمة حقيقية.
## شجرة مختصرة

```text
src/app/
├── layout.tsx                       Root layout + header/footer/providers
├── (store)/
│   ├── page.tsx                     /
│   ├── products/page.tsx            /products
│   ├── products/[slug]/page.tsx     /products/:slug
│   ├── categories/[slug]/page.tsx   /categories/:slug
│   ├── cart/page.tsx                /cart
│   └── checkout/page.tsx            /checkout
├── (account)/
│   ├── layout.tsx
│   ├── login/page.tsx               /login
│   ├── register/page.tsx            /register
│   ├── account/page.tsx             /account
│   ├── orders/page.tsx              /orders
│   └── orders/[id]/page.tsx         /orders/:id
├── api/
│   ├── auth/{login,logout,register,session}/route.ts
│   └── backend/[...path]/route.ts
├── sitemap.ts                       /sitemap.xml
├── robots.ts                        /robots.txt
├── loading.tsx / error.tsx / not-found.tsx
└── icon.svg                         /icon.svg
```

## صفحات المتجر والحساب

| Browser URL | الصلاحية | ملف الـroute الحقيقي | النوع والمكوّنات الأساسية | Django/API data path | SEO | الوصول والحالة |
|---|---|---|---|---|---|---|
| `/` | Public | `src/app/(store)/page.tsx` | Server Component؛ `ProductRail` client island و`ProductCard` | `getProducts()` → `GET /api/v1/catalog/products/`، و`getCategories()` | Metadata من root layout؛ محتوى SSR وقابل للفهرسة حسب `NEXT_PUBLIC_INDEX_SITE` | اللوجو. شغال؛ يعرض 10 featured fashion products في الـrail و8 cards |
| `/products` | Public | `src/app/(store)/products/page.tsx` | Server Component؛ `CatalogFilters`, `Pagination`, `ProductCard` | products/categories/brands public API | `generateMetadata`، canonical `/products`؛ faceted/search URLs عليها `noindex,follow` | Header: Shop all/Search. شغال |
| `/products?search=coat&category=coats-outerwear&ordering=name&page=2` | Public | نفس الملف السابق | URL state؛ مفيش route منفصل لكل filter | Query params بتروح لـDjango catalog endpoint | نفس canonical؛ filtered state غير مفهرس | من filters وpagination. شغال |
| `/products/[slug]` مثال `/products/clay-zip-hoodie` | Public | `src/app/(store)/products/[slug]/page.tsx` | Server page + `ProductGallery` و`PurchasePanel` client islands | `getProduct(slug)` و`getReviews(product.id)` | `generateMetadata`، canonical، absolute OG image، Product/Offer JSON-LD وBreadcrumb JSON-LD، و404 حقيقي | Product card أو quick preview. شغال وdirect reload مدعوم |
| `/categories/[slug]` مثال `/categories/hoodies-sweatshirts` | Public | `src/app/(store)/categories/[slug]/page.tsx` | Server Component + product grid/pagination | categories list ثم products filtered by parent/child category | dynamic title/description/canonical + Breadcrumb JSON-LD | Category cards والbreadcrumb. شغال |
| `/cart` | Authenticated data | `src/app/(store)/cart/page.tsx` | Page shell + `CartView` Client Component | `/api/backend/cart` و`/api/backend/cart/items/:id` | private/noindex من layout/page metadata | Header bag أو Add to bag. شغال؛ غير المسجل بياخد sign-in prompt |
| `/checkout` | Authenticated | `src/app/(store)/checkout/page.tsx` | `CheckoutView` Client Component | addresses، shipping methods، `checkout/preview`، `checkout` | `noindex` | من cart. شغال COD فقط وبيستخدم `Idempotency-Key` |
| `/login?next=/cart` | Public form | `src/app/(account)/login/page.tsx` | `AuthForm` Client Component | `POST /api/auth/login` → Django login/profile | `noindex` | Session controls أو protected prompt. شغال |
| `/register` | Public form | `src/app/(account)/register/page.tsx` | `AuthForm` Client Component | `POST /api/auth/register` → register ثم login | `noindex` | Session controls. شغال |
| `/account` | Authenticated data | `src/app/(account)/account/page.tsx` | `AccountDashboard` + `WishlistPanel` | session، `/api/backend/users/addresses`، `/api/backend/wishlist` | `noindex` | User icon. شغال |
| `/account#addresses` | Authenticated section | نفس `/account`؛ مفيش `page.tsx` مستقل | anchor لقسم saved addresses | GET/POST addresses | `noindex` | داخل account. شغال |
| `/account#wishlist` | Authenticated section | نفس `/account`؛ مفيش route مستقل | `WishlistPanel` | GET/DELETE wishlist؛ الإضافة من `PurchasePanel` | `noindex` | Heart في header أو المنتج. شغال |
| `/orders` | Authenticated | `src/app/(account)/orders/page.tsx` | `OrdersView` | `GET /api/backend/orders` | `noindex` | Account → View orders. شغال |
| `/orders/[id]` مثال `/orders/42?placed=1` | Owner only | `src/app/(account)/orders/[id]/page.tsx` | `OrderDetail` | GET order؛ POST `orders/:id/cancel` | `noindex` | Orders list أو redirect بعد checkout. شغال؛ return form غير منفذ |

مفيش Next staff/admin page. Django Admin موجود منفصل على backend URL `/admin/` ومش بيتقدّم على Next. مفيش route للـreturns أو staff dashboard حاليًا؛ النص داخل order detail بيذكر إن Django workflow موجود لكن storefront form لسه follow-up.

## Route Handlers وmetadata endpoints

| URL | المصدر | الدور | Upstream | الحماية والحالة |
|---|---|---|---|---|
| `POST /api/auth/login` | `src/app/api/auth/login/route.ts` | login BFF، يجيب profile ويحط JWT في HttpOnly cookies | `/api/v1/auth/login/`, `/api/v1/users/me/` | Same-origin mutation check؛ شغال |
| `POST /api/auth/register` | `src/app/api/auth/register/route.ts` | register ثم login تلقائي | `/api/v1/auth/register/`, `/api/v1/auth/login/` | Same-origin؛ شغال |
| `POST /api/auth/logout` | `src/app/api/auth/logout/route.ts` | blacklist refresh ثم يمسح cookies | `/api/v1/auth/logout/` | Same-origin؛ شغال |
| `GET /api/auth/session` | `src/app/api/auth/session/route.ts` | يرجّع user من access/refresh cookies | `/api/v1/users/me/` | no-store؛ refresh rotation؛ شغال |
| `/api/backend/[...path]` | `src/app/api/backend/[...path]/route.ts` | Allowlisted authenticated proxy للـcart/wishlist/addresses/checkout/orders وغيرها | `/api/v1/<allowed path>/` | HttpOnly JWT، rotation، same-origin للكتابة، `Cache-Control: no-store`؛ شغال |
| `/sitemap.xml` | `src/app/sitemap.ts` | يجمع كل product/category URLs من Django | public catalog | شغال؛ بيتبع index control |
| `/robots.txt` | `src/app/robots.ts` | يمنع الفهرسة افتراضيًا لحد ضبط `NEXT_PUBLIC_INDEX_SITE=true` | بدون upstream | شغال |
| `/media/:path*` | rewrite في `next.config.ts` | local same-origin media proxy إلى Django؛ مش Route Handler | `${DJANGO_API_URL}/media/:path*` | للتطوير؛ production يفضّل object storage/CDN |

`[...path]` Catch-all: مثل `/api/backend/orders/42/cancel` بيتحوّل داخليًا لقائمة segments. الـallowlist تمنع استخدام الـproxy كـopen proxy.

## ملفات التنفيذ ومسؤولية كل جزء

- `src/app/layout.tsx`: HTML root، metadata base، `SiteHeader`, `SiteFooter`, React Query providers.
- `src/app/(store)`: صفحات public commerce والـcart/checkout.
- `src/app/(account)`: صفحات auth/account/order؛ اسم المجموعة مش في URL.
- `src/features/showcase/product-rail.tsx`: circular 3D rail بيلف cyclically بالـdrag/swipe أو الأسهم؛ hover/focus بيحرّك القطعة للمنتصف، والقطعة النشطة بتفتح Quick Preview مع Escape/focus restoration.
- `src/features/catalog/product-card.tsx`: card/link/price/brand.
- `src/features/catalog/product-media.tsx`: الصورة الرئيسية وfallback.
- `src/features/catalog/product-gallery.tsx`: circular product-image orbit بنفس interaction الـrail؛ drag/swipe، أسهم، wrap من آخر صورة للأولى، وصورة نشطة كبيرة في المنتصف.
- `src/features/catalog/catalog-filters.tsx` و`pagination.tsx`: URL query state.
- `src/features/commerce/purchase-panel.tsx`: variant selection، stock، add-to-cart/wishlist.
- `src/features/commerce/variant-option-orbit.tsx`: الخيارات البصرية زي color/style/shape في circular swatch orbit؛ الـdrag والأسهم يغيّروا الـvariant الحقيقي، بينما size يفضل اختيار قياس مباشر.
- `src/features/commerce/wishlist-panel.tsx`: عرض/حذف wishlist داخل account.
- `src/features/auth`: forms، session controls، profile/addresses.
- `src/features/cart`, `checkout`, `orders`: flows العميل بعد تسجيل الدخول.
- `src/shared/api/server.ts`: server-only public Django fetchers مع Next revalidation/tags.
- `src/shared/api/client.ts`: same-origin browser requests للـBFF.
- `src/shared/api/auth-session.ts`: HttpOnly cookies، refresh rotation، origin validation.
- `src/shared/api/generated/schema.d.ts`: generated من `backend/schema.yml`؛ ممنوع يتعدل يدويًا.
- `src/shared/lib/urls.ts`: media URL normalization؛ `/media/*` يتحول same-origin، وexternal CDN URL يفضل external.
- `src/shared/ui/resilient-image.tsx`: fallback فعلي بعد browser image error مع dev diagnostic.
- `src/shared/ui`: buttons/fields/header/footer وdesign primitives.
- `src/app/globals.css`: Tailwind theme tokens، canvas/ink/sage/clay، typography، media aspect treatment.
- `frontend/public`: build-time static assets فقط؛ حاليًا مفيش catalog photography هنا.
- `backend/product/management/demo_fashion/assets`: المصادر المحلية الثابتة اللي seed بينسخها لـDjango storage.
- `backend/media` أو `DJANGO_MEDIA_ROOT`: runtime Django media؛ مش source fixture ومش المفروض يعتمد على `%TEMP%` في التطوير العادي.

مفيش `middleware.ts` حاليًا. حماية صفحات الحساب معمولة من خلال BFF/API ownership والـClient UI؛ الـbackend يفضل authority النهائية للصلاحيات.

## Data flow 1: Home إلى Cart

```text
GET /
  -> Server Component getProducts(category=apparel, page_size=100)
  -> Django CatalogProductViewSet + serializers
  -> primary_image / variants / live stock
  -> ProductRail client island
  -> Quick Preview dialog + PurchasePanel
  -> /products/clay-zip-hoodie (SSR + gallery + JSON-LD)
  -> POST /api/backend/cart/items
  -> BFF reads HttpOnly access cookie
  -> Django POST /api/v1/cart/items/
  -> /cart
```

## Data flow 2: Login إلى Order Details

```text
/login -> POST /api/auth/login -> Django auth/login
       -> HttpOnly access + refresh cookies
/cart -> GET /api/backend/cart -> Django customer cart
/account#addresses -> POST /api/backend/users/addresses
/checkout -> GET addresses + shipping
          -> POST /api/backend/checkout/preview (authoritative total)
          -> POST /api/backend/checkout + Idempotency-Key (COD)
          -> /orders/:id?placed=1
          -> GET /api/backend/orders/:id
```

## مصطلحات App Router من المشروع

- Browser route `/products/clay-zip-hoodie` مش هو file path. الملف هو `src/app/(store)/products/[slug]/page.tsx`.
- `[slug]`: dynamic segment نصي؛ `[id]` رقم order بيتراجع ownership بتاعه في Django.
- `(store)`: grouping فقط؛ URL مش `/store/products`.
- `page.tsx`: UI الخاصة بمسار.
- `layout.tsx`: wrapper مشترك بيستمر بين صفحات المجموعة.
- `route.ts`: HTTP handler، مش React page.
- `loading.tsx`, `error.tsx`, `not-found.tsx`: loading/error/404 boundaries.
- Server Component: بيجيب public data وHTML على السيرفر؛ مثال product page.
- Client island: ملف عليه `"use client"` للتفاعل؛ مثال `ProductRail`, `ProductGallery`, `CheckoutView`.

