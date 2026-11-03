# API examples

## Register and login

```http
POST /api/v1/auth/register/
Content-Type: application/json

{"username":"sara","email":"sara@example.com","first_name":"Sara","last_name":"Ali","password":"A-strong-password-2026"}
```

```http
POST /api/v1/auth/login/
Content-Type: application/json

{"username":"sara","password":"A-strong-password-2026"}
```

Use `Authorization: Bearer <access>` below.

## Browse and select a SKU

```http
GET /api/v1/catalog/products/?category=electronics&available=true&ordering=min_price
```

The detail response exposes active variants such as:

```json
{"id":42,"sku":"CAIRO-BLK-128","option_values":{"color":"black","storage":"128GB"},"price":"12999.00","stock":20,"is_active":true}
```

## Address, cart and quote

```http
POST /api/v1/users/addresses/

{"recipient":"Sara Ali","phone":"+201000000000","line1":"10 Nile St","city":"Cairo","state":"Cairo","postal_code":"11511","country":"EG","is_default":true}
```

```http
POST /api/v1/cart/items/

{"variant_id":42,"quantity":2}
```

```http
POST /api/v1/checkout/preview/

{"address_id":3,"shipping_method_id":1,"coupon_code":"WELCOME10","points":100}
```

## Idempotent checkout

```http
POST /api/v1/checkout/
Idempotency-Key: 6cf68453-883d-42ce-b66a-9f2bd4051e65
Content-Type: application/json

{"address_id":3,"shipping_method_id":1,"coupon_code":"WELCOME10","points":100}
```

An identical retry returns the same order with 200. A changed body with that key returns 400. The client never sends price, total, stock, payment status, or discount amount.

## Orders and cancellation

```http
GET /api/v1/orders/?status=pending
POST /api/v1/orders/12/cancel/
GET /api/v1/orders/12/timeline/
```

## Return and staff processing

```http
POST /api/v1/orders/returns/

{"order_item":91,"quantity":1,"reason":"Item arrived damaged"}
```

```http
POST /api/v1/orders/returns/7/decide/
Authorization: Bearer <staff-access>

{"status":"approved","staff_note":"Return inspected"}
```

Approval creates a pending cash refund. Staff explicitly records completion:

```http
POST /api/v1/admin/refunds/5/complete/
Authorization: Bearer <staff-access>
```

## Staff order and COD flow

```http
POST /api/v1/orders/12/transition/
Authorization: Bearer <staff-access>

{"status":"shipped","note":"Handed to courier"}
```

```http
POST /api/v1/admin/payments/12/collect/
Authorization: Bearer <staff-access>
```
