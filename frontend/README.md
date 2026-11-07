# Atelier Cairo storefront

التوثيق العربي التفصيلي:

- [خريطة كل browser routes وربطها بالملفات والـAPIs](docs/FRONTEND_ROUTE_MAP_AR.md)
- [دليل الـarchitecture والتشغيل والصور والاختبارات](docs/FRONTEND_ARCHITECTURE_AR.md)

SEO-first Next.js App Router storefront for the Django e-commerce API in this repository. Public catalog content is rendered on the server; interactive and private flows use focused client islands and a same-origin BFF.

## Local setup

1. Start Django on `http://127.0.0.1:8000` with an isolated development database.
2. For the fashion demo, run `python manage.py seed_demo_store` against that development database only.
3. Copy `.env.example` to `.env.local`. Keep `NEXT_PUBLIC_INDEX_SITE=false` outside the canonical production domain.
4. Install and run:

```bash
npm install
npm run generate:api
npm run dev
```

Open `http://localhost:3000`. The signature garment rail is on `/`; conventional shopping remains at `/products`.

## Architecture

- `src/app`: App Router pages, metadata, sitemap/robots and BFF Route Handlers.
- `src/features/showcase`: garment rail and reversible quick preview.
- `src/features/catalog`: product grid, filters, gallery and pagination.
- `src/features/commerce`: shared variant selection and purchase UI.
- `src/features/auth`, `cart`, `checkout`, `orders`: private Django-backed flows.
- `src/shared/api/generated`: generated from `backend/schema.yml`; do not hand-edit.
- `src/shared/api`: public server fetches, BFF client calls, normalized errors and JWT cookie helpers.
- `src/shared/ui`: shadcn-style local primitives configured by `components.json`.

## Rendering, caching and auth

Public catalog requests are server-side and revalidated every five minutes with cache tags. Product/category HTML, links, prices and metadata exist without client JavaScript. Cart, account, checkout, orders and token refreshes go through same-origin Route Handlers with `no-store`.

JWT access and rotating refresh tokens live in `HttpOnly`, `SameSite=Lax` cookies (`Secure` in production). Mutating BFF requests reject cross-site origins. Django permissions remain authoritative.

## SEO

- Permanent `/products/[slug]` pages with genuine 404 handling.
- Product/Offer and Breadcrumb JSON-LD from live API data.
- Dynamic Open Graph/Twitter metadata, `sitemap.xml` and environment-aware `robots.txt`.
- Faceted product URLs are `noindex,follow` and canonicalize to `/products`.
- Account, cart, checkout, order and API paths are excluded from indexing.

Set `NEXT_PUBLIC_SITE_URL` to the production origin and only then set `NEXT_PUBLIC_INDEX_SITE=true`.

## Verification

```bash
npm run typecheck
npm run lint
npm run test:run
npm run build
```

Playwright requires both an isolated seeded Django API and the Next server:

```bash
npx playwright install chromium
npm run test:e2e
```

## Demo media and current limits

The fashion seed uses original transparent SVG illustrations under `backend/product/management/demo_assets`. They are explicit development placeholders, not product photography. Replace them through Django admin with supplied/licensed cutouts before launch.

Only Cash on Delivery is presented because no card gateway exists. A customer return form and staff dashboard remain follow-ups; their backend APIs are not misrepresented as completed UI.
