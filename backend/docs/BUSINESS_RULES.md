# Business rules

## Pricing

- Currency is EGP; calculations use `Decimal` and quantize to 0.01.
- Formula: merchandise subtotal → coupon discount → loyalty discount → shipping → zero tax.
- Shipping and tax are not discounted and do not earn points.
- Quote is non-binding. Checkout recomputes everything under locks.

Example: 2 × 100.00 = 200.00; 10% coupon = 20.00; 100 points = 10.00; shipping = 20.00; total = 190.00 EGP.

## Catalog and inventory

- A SKU sells only when its product and variant are active and sufficient stock exists.
- Cart addition validates current availability but does not reserve stock.
- Checkout deducts stock. Cancellation and approved return restore it once and write movements.
- Staff adjustments reject zero delta and negative resulting stock.

## Shipping

- Checkout address must belong to the customer.
- Method and zone must be active and serve the address country and, when configured, state.
- Address, method name and fee are snapshotted on the order.

## Coupons

- One coupon per order; no coupon stacking.
- Code is normalized uppercase. Active window, minimum, scope, cap, global limit and per-user limit are checked server-side.
- Coupon row is locked during checkout. Cancellation releases its redemption slot.

## Loyalty

- 10 points redeem for 1 EGP. Requested points must be a non-negative multiple of ten and cannot exceed post-coupon merchandise.
- Eligible delivered + paid merchandise earns `floor(net merchandise / 10)` points exactly once.
- Checkout immediately debits redeemed points; transaction rollback restores all side effects automatically.
- Cancellation returns all redeemed points.
- Partial return returns redeemed points proportionally and claws back earned points proportionally.
- If earned points were spent, available balance stops at zero and the rest becomes `outstanding_clawback`; future earnings repay debt first.
- Every event has a unique key. Staff adjustments require a reason and cannot create negative available balance.

## Orders and idempotency

- State transitions: `pending → confirmed → shipped → delivered → returned`; pending/confirmed may cancel.
- Cancellation is a transition, never deletion. Stock/coupon/points reverse once.
- Checkout requires an `Idempotency-Key`. Same user/key/body returns the original order; changed payload is rejected.
- Items, prices, options, address, shipping, discounts and totals are historical snapshots.

## Payments

- COD starts pending and can be collected only for shipped/delivered orders by staff.
- Repeated collection is idempotent. Loyalty earning occurs only when both delivered and paid are true, regardless of event order.
- There is no customer endpoint that marks payment successful.

## Returns and refunds

- Only owned delivered order items can be returned.
- Requested quantities across non-rejected returns cannot exceed purchased quantity.
- Staff approval restores inventory, calculates a proportional net-merchandise refund, adjusts loyalty, creates timeline/audit records, and creates a pending cash refund.
- Staff completion is idempotent and updates payment to partially/full refunded. It records internal cash handling, not external gateway evidence.
