# E-commerce API

A learning and portfolio project that implements a small e-commerce backend with Django REST Framework. It includes JWT authentication, a public product catalog, persistent customer carts, transactional cash-on-delivery checkout, customer-scoped orders, and product reviews.

## Features

- Registration, JWT login and refresh, profile updates, and token-based password reset.
- Public product listing and detail endpoints with category, name, brand, and price filters and pagination.
- Administrator-only product create, update, and delete operations.
- Persistent per-user cart with database-priced totals and stock checks.
- Checkout from the cart, price snapshots, atomic inventory deduction, and order cancellation with inventory restoration.
- Customer-scoped order history and valid processing, shipping, delivery, and cancellation transitions.
- One review per customer and product through the API, ratings from 1 through 5, and stored average product ratings.
- OpenAPI schema and Swagger UI.

## Stack and structure

Python 3.10–3.14, Django 5.2 LTS (minimum patch 5.2.18), Django REST Framework 3.16, Simple JWT, django-filter, drf-spectacular, pytest, Ruff, SQLite for local development, and MySQL 8.4 support through environment settings. Django 5.2 supports Python 3.10–3.14; the CI workflow uses Python 3.12.

`account/` handles users and profiles; `product/` contains catalog and review models and APIs; `order/` contains orders, cart records, and checkout services; `emarket/` contains project configuration and root URLs. Views handle HTTP and permissions, serializers validate input, and `order/services.py` owns the multi-step checkout and cancellation transactions.

## Local setup

Python 3.10 or later is recommended. From a clean checkout:

```powershell
uv sync
Copy-Item .env.example .env
# Set DJANGO_SECRET_KEY in .env before using the project outside local development.
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

`uv run` also synchronizes dependencies on first use. The `dev` dependency group includes pytest and Ruff. To install the optional MySQL driver, run `uv sync --extra mysql`.

Alternatively, with pip:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Set `DJANGO_SECRET_KEY` in `.env` to a new random value. The default database is SQLite, so the project runs locally without a database server or native database driver. To use MySQL, install `requirements-mysql.txt`, set `DB_ENGINE=django.db.backends.mysql`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`. On Windows, install the MySQL client development prerequisites required by `mysqlclient` first.

Apply migrations and start Django:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

In development, password reset messages are printed to the console. Configure `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_PORT`, and `EMAIL_USE_TLS` to send mail through SMTP. The reset endpoint always returns the same response whether the email exists.

## API overview

Register with `POST /api/register/` and JSON such as `{"first_name":"Sam", "last_name":"Lee", "username":"samlee", "email":"sam@example.com", "password":"a-long-unique-password"}`. Obtain tokens with `POST /api/token/` and `{"username":"samlee", "password":"a-long-unique-password"}`. Send the access token as `Authorization: Bearer <access>` and refresh with `POST /api/token/refresh/` and `{"refresh":"<refresh-token>"}`. Authenticated users can view `/api/userinfo/` and update `/api/userinfo/update/`.

Catalog: `GET /api/products/?name=phone&category=Phones&minprice=10&maxprice=100`, `GET /api/products/{id}/`. Staff use `POST /api/new_product/`, `PUT /api/products/update/{id}/`, and `DELETE /api/products/delete/{id}/`.

Cart: `GET /api/cart/`; add items with `POST /api/cart/` and `{"product_id": 1, "quantity": 2}`; update with `PUT /api/cart/items/{item_id}/` and `{"quantity": 1}`; remove with `DELETE` on that item path. Totals and prices are calculated from current product rows.

Checkout: `POST /api/orders/new/` with `city`, `zip_code`, `street`, `state`, `country`, and `phone_no`. The server checks the saved cart and ignores any client-supplied item or price fields. Customers can list `/api/orders/`, view `/api/order/{id}/`, and cancel a processing order with `DELETE /api/order/{id}/delete/`. Staff can advance order status using `PUT /api/order/{id}/process/` with `{"status":"Shipped"}` or `{"status":"Delivered"}`.

Reviews: authenticated users submit or update via `POST /api/{product_id}/review/` with `{"rating": 5, "comment":"Good"}`, and delete their review via `DELETE /api/{product_id}/review/delete/`.

Password reset starts with `POST /api/forget_password/` and `{"email":"sam@example.com"}`. The emailed link includes a token; submit `{"password":"a-new-long-unique-password", "confirmPassword":"a-new-long-unique-password"}` to `POST /api/reset_password/{token}`. The API returns the same message for known and unknown email addresses.

Interactive documentation is available at `/api/docs/`; the OpenAPI document is at `/api/schema/`. Invalid input returns field-level HTTP 400 responses. Unauthorized users receive 401/403, and orders belonging to another customer are hidden with 404.

## Tests and CI

Run the suite with `python -m pytest`. Django's test runner can also run the app tests. Pytest's optional result cache is disabled because it is not needed by this suite and can fail in restricted workspaces. GitHub Actions checks Django configuration and migration consistency, confirms its database connection is MySQL, runs pytest, checks Ruff on the changed application modules, and verifies formatting.

SQLite supports local development and functional tests. It does not provide the row-locking guarantees used by MySQL, so both checkout locking tests are skipped on SQLite. GitHub Actions runs the suite against MySQL 8.4: one test checks that checkout issues `SELECT FOR UPDATE`, and another races two checkouts for the final unit and verifies only one order succeeds. This is a focused concurrency test, not a high-volume stress test.

## Engineering decisions and limitations

Checkout trusts only the persistent cart and current product prices, creates order and item records in one transaction, snapshots unit prices, and decrements stock with a conditional database update. Cancellation is a state transition and restores stock once. There is no real payment processing; orders use Cash on Delivery. Email delivery needs SMTP configuration. Product ratings retain a legacy-compatible zero value for products without reviews. This project is not deployed or represented as production-secure; production use still requires environment-specific review, secrets, a supported database, HTTPS, logging, backups, and operational controls.

The integrity migrations do not rewrite legacy data. They stop with a clear error if duplicate reviews, invalid review ratings, negative order totals, or invalid order items exist; reconcile those rows before retrying the migration.

Earlier versions included hard-coded Django and Mailtrap credentials. They have been removed from the application settings. Rotate them if they were ever used outside this local project or committed to a remote repository; this work does not rewrite Git history.

