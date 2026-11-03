# Testing

Tests are organized by app under `account/tests/`, `product/tests/`, and `order/tests/`. They cover models/constraints, API permissions and ownership, transactional services, full workflows, exact money, reversals and PostgreSQL concurrency.

```powershell
uv run pytest
uv run pytest account/tests
uv run pytest order/tests/test_workflows.py
uv run coverage run -m pytest
uv run coverage report -m
```

API tests use DRF `APIClient`; service tests inspect resulting database rows and ledgers. Integration tests exercise registration/address/catalog/cart/quote/checkout/status/payment/review/return/refund/reporting behavior.

Concurrency tests use `TransactionTestCase`, separate thread connections and barriers. They test final stock/coupon competition and same-customer cart/loyalty double spend. They are skipped when `has_select_for_update` is false; a SQLite pass is not concurrency evidence. CI provisions PostgreSQL 17 so these tests execute there.

Latest local result: **20 passed, 3 skipped** on SQLite. The three skips are PostgreSQL-only races covering stock/coupon, cart/loyalty, and duplicate payment/refund processing. Measured coverage: **87% overall** and **90% for `order/services.py`**.

Quality gates:

```powershell
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run ruff check account product order emarket
uv run ruff format --check account product order emarket
uv run python manage.py spectacular --file schema.yml --validate
```

Tests should assert both response and durable side effects: order count, stock, movements, coupon redemptions, wallet balance, ledger event uniqueness, timelines, payment/refund state and audit records. Never weaken a race or rollback assertion to make SQLite pass.
