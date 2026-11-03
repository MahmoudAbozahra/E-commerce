# API reference

Base path: `/api/v1/`. JWT bearer authentication is required unless marked public. Collection responses are paginated as `count`, `next`, `previous`, `results`.

| Method | Path | Role | Purpose / important fields |
|---|---|---|---|
| POST | `/auth/register/` | Public | `username,email,password,first_name,last_name` |
| POST | `/auth/login/` | Public | Username/password; returns access/refresh |
| POST | `/auth/refresh/` | Public | Rotates refresh token |
| POST | `/auth/logout/` | Customer | Blacklists `refresh` |
| POST | `/auth/password/change/` | Customer | Current and new password |
| POST | `/auth/password/reset/request/` | Public | Non-enumerating email request |
| POST | `/auth/password/reset/confirm/` | Public | One-time token and password |
| GET/PATCH | `/users/me/` | Customer | Profile |
| CRUD | `/users/addresses/` | Owner | Saved delivery addresses |
| GET | `/notifications/` | Owner | In-app notifications |
| POST | `/notifications/{id}/read/` | Owner | Mark read |
| GET | `/admin/audit-logs/` | Staff | Sensitive-operation audit trail |
| GET | `/catalog/categories/` | Public | Active categories |
| GET | `/catalog/brands/` | Public | Active brands |
| GET | `/catalog/products/` | Public | Product list/search/filter/order |
| GET | `/catalog/products/{slug}/` | Public | Product detail with variants/images |
| CRUD | `/wishlist/` | Customer | Unique owned wishlist items |
| GET/DELETE | `/cart/` | Customer | Retrieve/clear cart |
| CRUD | `/cart/items/` | Customer | `variant_id,quantity` |
| GET | `/shipping/methods/` | Public | Active methods |
| POST | `/checkout/preview/` | Customer | `address_id,shipping_method_id,coupon_code,points` |
| POST | `/checkout/` | Customer | Same fields plus `Idempotency-Key` header |
| GET | `/orders/` | Customer/staff | Own/all orders; `reference,status` filters |
| GET | `/orders/{id}/` | Owner/staff | Order snapshots and payments |
| POST | `/orders/{id}/cancel/` | Owner/staff | Valid cancellation |
| GET | `/orders/{id}/timeline/` | Owner/staff | Order status history |
| POST | `/orders/{id}/transition/` | Staff | `status,note` |
| POST | `/coupons/validate/` | Customer | `code,address_id,shipping_method_id` against cart |
| GET | `/loyalty/wallet/` | Customer | Balance and clawback |
| GET | `/loyalty/transactions/` | Customer | Ledger |
| GET, POST | `/orders/returns/` | Customer/staff | Create a return request or list owned/all requests; requests cannot be directly edited or deleted |
| GET | `/orders/returns/{id}/timeline/` | Owner/staff | Return timeline |
| POST | `/orders/returns/{id}/decide/` | Staff | `status=approved|rejected,staff_note` |
| CRUD | `/catalog/products/{id}/reviews/` | Public read / verified owner write | Rating 1–5 and comment |
| POST | `/catalog/products/{id}/reviews/{review}/moderate/` | Staff | `is_approved` |
| CRUD | `/admin/catalog/categories/` | Staff | Category management |
| CRUD | `/admin/catalog/brands/` | Staff | Brand management |
| CRUD | `/admin/catalog/products/` | Staff | Product management |
| CRUD | `/admin/catalog/variants/` | Staff | Variant management; stock is read-only |
| CRUD | `/admin/catalog/images/` | Staff | Product images and primary ordering |
| POST | `/admin/catalog/variants/{id}/adjust_stock/` | Staff | `delta,reason` |
| CRUD | `/admin/coupons/` | Staff | Coupon configuration and eligibility |
| CRUD | `/admin/shipping/zones/` | Staff | Country/state delivery zones |
| CRUD | `/admin/shipping/methods/` | Staff | Flat-rate methods |
| GET | `/admin/payments/` | Staff | Payments |
| POST | `/admin/payments/{id}/collect/` | Staff | Idempotent COD collection |
| GET | `/admin/refunds/` | Staff | Refund records |
| POST | `/admin/refunds/{id}/complete/` | Staff | Idempotent cash refund completion |
| POST | `/admin/loyalty/adjustments/` | Staff | `user_id,delta,reason` |
| GET | `/admin/reports/summary/` | Staff | Revenue, statuses, SKU sales, low stock, liability |
| GET | `/health/` | Public | Liveness |

Product query parameters: `search`, `category`, `brand`, `min_price`, `max_price`, `available`, `ordering`. Allowed ordering: `created_at`, `name`, `min_price`, with optional `-` prefix.

Common statuses: 200 read/replay, 201 create, 204 no content, 400 validation/business rejection, 401 unauthenticated, 403 role denial, 404 hidden foreign resource.

Errors use:

```json
{"error":{"code":"invalid","detail":{"quantity":["Requested quantity exceeds stock."]}}}
```

The authoritative machine-readable contract is `/api/schema/` and `schema.yml`.
