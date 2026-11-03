# Database design

PostgreSQL is the reference database. All foreign keys use deliberate deletion policies, money uses `DecimalField`, datetimes are timezone-aware, and important global invariants have database constraints.

```mermaid
erDiagram
    USER ||--|| PROFILE : has
    USER ||--o{ ADDRESS : owns
    USER ||--o{ NOTIFICATION : receives
    CATEGORY ||--o{ CATEGORY : parent
    CATEGORY ||--o{ PRODUCT : contains
    BRAND ||--o{ PRODUCT : owns
    PRODUCT ||--o{ PRODUCT_IMAGE : has
    PRODUCT ||--o{ PRODUCT_VARIANT : has
    PRODUCT_VARIANT ||--o{ INVENTORY_MOVEMENT : records
    USER ||--|| CART : owns
    CART ||--o{ CART_ITEM : contains
    PRODUCT_VARIANT ||--o{ CART_ITEM : selected
    USER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_ITEM : snapshots
    ORDER ||--o{ ORDER_STATUS_HISTORY : timeline
    ORDER ||--o{ PAYMENT : payments
    COUPON ||--o{ COUPON_REDEMPTION : usage
    USER ||--|| LOYALTY_WALLET : owns
    LOYALTY_WALLET ||--o{ LOYALTY_TRANSACTION : ledger
    ORDER_ITEM ||--o{ RETURN_REQUEST : return
    RETURN_REQUEST ||--o{ RETURN_STATUS_HISTORY : timeline
    RETURN_REQUEST ||--o| REFUND : refund
```

## Account models

- `User`: Django `AbstractUser`; nullable email for internal accounts but API registration requires it. Non-empty email is normalized lowercase and database-unique.
- `Profile`: one-to-one phone and hashed password-reset token metadata.
- `Address`: owned delivery address. Partial unique constraint allows at most one default address per user.
- `Notification`: owner-scoped in-app message, indexed by owner/read/time.
- `AuditLog`: append-only staff action record; indexed by action/time.

## Catalog and inventory

- `Category`: unique slug, protected self-parent hierarchy, active state and sort order. Application validation walks ancestors to reject cycles.
- `Brand`: unique name/slug, optional image and description.
- `Product`: protected category/brand links and draft/active/archive state. Index covers status/category/brand.
- `ProductVariant`: unique SKU and per-product normalized option signature; non-negative price; authoritative stock.
- `ProductImage`: ordered media; conditional unique constraint permits one primary image per product.
- `InventoryMovement`: signed non-zero delta, reason, actor and reference. Variant deletion is protected.
- `Review`: one per user/product, rating check 1–5, approval state.
- `WishlistItem`: unique user/product pair.

## Commerce

- `Cart`: one per user. `CartItem` is unique by cart/variant and quantity is positive.
- `ShippingZone`: configured countries/states. `ShippingMethod` has unique code and non-negative flat fee.
- `Coupon`: normalized unique code, type/value/cap/minimum/window/limits and optional product/category eligibility.
- `Order`: user, independent order state, EGP totals, coupon/points/shipping/tax snapshots, JSON address snapshot, reversal flags and stable reference.
- `OrderItem`: immutable product name, SKU, options, unit price, quantity and line total snapshots; variant may later be removed via `SET_NULL`.
- `OrderStatusHistory`: append-only status event.
- `CheckoutAttempt`: unique `(user, key)`, request hash and one resulting order.
- `CouponRedemption`: one per order with release timestamp for cancellation.
- `LoyaltyWallet`: non-negative available balance and outstanding clawback debt.
- `LoyaltyTransaction`: signed balance delta, kind, globally unique event key, order and metadata. Zero delta is allowed for debt-only events.
- `Payment`: persisted COD state, amount/currency and unique transaction reference.
- `ReturnRequest`: item, quantity, reason, decision, stock/refund facts. Positive quantity constraint.
- `ReturnStatusHistory`: append-only return timeline.
- `Refund`: one per return, positive amount, unique reference, pending/completed/rejected cash state.

`PROTECT` is used where deletion would erase commercial meaning. User deletion generally cascades private working data but orders retain nullable historical ownership. Operational records should normally be deactivated rather than deleted.
