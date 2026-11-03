# Codebase walkthrough

## Suggested reading order

1. `emarket/settings.py` and `emarket/urls.py`
2. `account/urls.py`, `product/urls.py`, `order/urls.py`
3. Each app's `views.py` and `serializers.py`
4. `order/services.py` and `product/services.py`
5. `order/selectors.py`
6. `account/models.py`, `product/models.py`, `order/models.py`
7. App `tests/` directories
8. Migrations, admin and seed command

## 1. Request entry

Django loads `emarket.urls`. `/api/v1/` is delegated to the three canonical app URL modules. DRF routers generate standard viewset list/detail/action paths; explicit paths handle auth, quote, checkout, wallet and reports.

## 2. Authentication and permissions

`JWTAuthentication` is the global DRF authentication class. A public endpoint explicitly uses `AllowAny`; private views use `IsAuthenticated`; management operations use `IsAdminUser`. Owner isolation is enforced by filtered querysets such as `AddressViewSet.get_queryset`, `OrderViewSet.get_queryset`, and `ReturnViewSet.get_queryset`, so a foreign ID resolves as 404.

## 3. Serializer validation

Serializers convert JSON into typed validated data. Ownership-aware fields replace their default querysets at initialization—for example checkout address IDs are limited to `request.user.addresses`. Serializers validate shape and local rules; they do not claim that stock/coupon/balance remains valid until the service locks current rows.

## 4. Views and services

A view validates input, invokes one service, and serializes the result. Example: `CheckoutView.post` validates `CheckoutRequestSerializer`, forwards user/address/method/coupon/points/key to `checkout`, then returns 201 or replay 200.

Transactional writes belong in:

- `product.services.adjust_inventory`
- `order.services.checkout`
- `transition_order`, `collect_cod`
- `create_return_request`, `decide_return`, `complete_refund`
- `adjust_loyalty`

Read composition belongs in `order.selectors`, while straightforward model querysets remain close to their view.

## 5. Transactions and models

`@transaction.atomic` creates all-or-nothing boundaries. `select_for_update()` prevents concurrent transactions from changing the same user/cart/SKU/coupon/wallet/payment/refund while a decision is made. Database constraints still protect uniqueness, positive quantities, non-negative money and one-to-one events.

Services create explicit side-effect records: inventory movements, order/return timelines, coupon redemptions, loyalty transactions and audit logs. Notifications use `transaction.on_commit`, so rolled-back work cannot create ghost messages.

## 6. Checkout walkthrough

`checkout()`:

1. Validates key length and locks the user, serializing that customer's cart/wallet operations.
2. Hashes the price-relevant request and checks `CheckoutAttempt`.
3. Calls `calculate_quote(..., lock=True)`.
4. Locks cart lines and variants in stable order and validates product/variant activity and stock.
5. Validates the address against the shipping zone, coupon limits and wallet balance.
6. Creates order/address/shipping/money snapshots and order items.
7. Deducts stock and writes movements; consumes coupon/points with unique records.
8. Creates pending COD payment and initial timeline event.
9. Clears the cart and links the idempotency attempt to the order.
10. Schedules the notification after commit.

Any exception rolls back every database write.

## 7. Response and error flow

Successful model results are serialized by DRF. Expected service rejection raises `ValidationError`. Permissions produce 401/403, owner-scoped querysets produce 404, and `emarket.exceptions.api_exception_handler` wraps handled errors consistently. Avoid broad exception handling; unexpected faults should be visible to monitoring.

## 8. Debugging a failing request

1. Confirm route with `python manage.py show_urls` if installed or Django `resolve()`.
2. Check authentication header and permission class.
3. Inspect serializer errors in the response envelope.
4. Reproduce through the smallest relevant test with `pytest -vv -s`.
5. Inspect service preconditions and transaction side-effect rows.
6. For concurrency issues, reproduce on PostgreSQL—not SQLite—and inspect locks/transaction boundaries.
7. Compare runtime schema at `/api/schema/` with the request.

## 9. Adding an endpoint

For a read endpoint: create a selector if the query is reused or aggregate-heavy, define an output serializer, add a thin view with explicit permission, register it in the app's `urls.py`, and test public/owner/staff scopes.

For a write endpoint: define input serializer, put multi-row logic in a service with an explicit transaction, add constraints/idempotency where necessary, call it from the view, document OpenAPI, and test success, invalid input, unauthorized access, rollback, replay and races.

## 10. Adding a business rule

Decide which layer owns enforcement:

- Database constraint for universal row/global invariants.
- Model validation for structural rules such as category cycles.
- Serializer for request-local syntax and owner-limited choices.
- Service for time-sensitive, cross-row or financial rules.
- Permission/queryset for role and object visibility.

Then add a negative test proving the rule cannot be bypassed through the API or concurrent service call.

## 11. Writing tests

- Model tests assert constraints with `IntegrityError` inside a nested atomic block.
- API tests use `APIClient` and assert status, response, ownership and forbidden fields.
- Service tests assert all affected rows and ledger/event uniqueness.
- Integration tests exercise a complete customer/staff workflow.
- Concurrency tests use `TransactionTestCase`, separate connections, barriers and PostgreSQL feature guards.

Keep fixtures realistic and monetary assertions exact `Decimal` values.
