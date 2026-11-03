# Completed implementation plan

- [x] Audit settings, apps, models, URLs, services, tests, migrations, CI and docs.
- [x] Remove legacy/v2 modules, multiline-hidden code, compatibility aliases and wildcard imports.
- [x] Establish one canonical Django module set per app.
- [x] Introduce fresh-schema custom User with unique normalized email.
- [x] Keep dynamic catalog, SKU inventory, wishlist and verified reviews.
- [x] Move inventory, checkout, order, loyalty, return and refund writes into services.
- [x] Move composed order/report reads into selectors.
- [x] Add shipping-zone validation, same-user checkout serialization, return timelines and return loyalty policy.
- [x] Regenerate clean first-party initial migrations only.
- [x] Expand model/API/service/integration/concurrency tests.
- [x] Rewrite English/Arabic and focused technical documentation.
- [ ] Execute PostgreSQL-only race tests locally if a Docker/PostgreSQL daemon becomes available; CI is configured to run them.

Local verification: 20 passed, 3 PostgreSQL-only skips, 87% measured coverage, fresh migrations and double seed succeeded, Django/Ruff/OpenAPI/deployment checks passed.

Destructive development-only actions: obsolete first-party migration source files and legacy backend modules were removed and clean initial migrations regenerated. No Django/contrib migration, frontend file, secret, or database was deleted. The local `db.sqlite3` was identified as zero bytes and left untouched.
