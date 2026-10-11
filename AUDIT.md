# Initial repository audit

This review was performed against the existing working tree before implementation. The project apps are `account`, `product`, and `order`; `manage.py` points to the available `emarket` settings package. The working tree already had the old `Ecommerce/` package and tracked SQLite database deleted, with `emarket/` present as an untracked replacement. Those pre-existing changes were preserved.

## Findings by priority

### High

- **Checkout trusted client prices and quantities.** The order endpoint summed client-supplied prices, accepted arbitrary product IDs and quantities, and deducted stock without checking availability. A failure partway through could leave an order and inventory partially updated.
- **Order authorization was missing.** Authenticated customers could list all orders, retrieve another customer's order, or delete it. The order list is now customer-scoped and detail/cancel checks ownership.
- **Credentials were embedded in settings.** The Django secret key and SMTP account values were hard-coded, and the database default used a local root account. Environment-backed settings and `.env.example` replace those values. Rotate the old SMTP credentials and Django key if they were used or published.
- **Sensitive product fields and review logic were unsafe.** Product updates trusted review ratings and used creator ownership in addition to admin authorization. Reviews rejected ratings 1 and 5, wrote to a nonexistent `ratings` attribute, and had no proper average refresh on deletion.

### Medium

- **No persistent cart or checkout lifecycle existed.** There was no cart, trusted price snapshot, cancellation transition, or inventory restoration. These are now implemented in the order app.
- **Account validation was incomplete.** Registration checked email against the username column, profile updates indexed unchecked request keys and accepted password/role changes, and password reset revealed whether an email existed. These paths now validate input, preserve role/password fields during profile edits, and return a generic reset response.
- **Catalog behavior did not match the public API description.** The default permission was authenticated-only, pagination was fixed at two products, filtering was incomplete, and product mutation used ad hoc field assignment. Public access, filters, pagination, and serializer validation are now explicit.
- **Schema integrity and migrations needed correction.** Product ratings had a string default, monetary totals used integers, and quantity/price constraints were absent. Additive migrations now improve these fields and introduce cart tables and integrity checks.

The new constraint migrations preflight legacy rows and stop without changing data if they find invalid values; those rows require explicit reconciliation before an upgrade can continue.

### Lower

- **Tests, CI, setup instructions, and API schema were absent or superficial.** The existing app tests were empty. The project now has behavioral tests, dependency/tool configuration, a MySQL CI job, and OpenAPI/Swagger endpoints.
- **Generated artifacts were tracked.** Python bytecode was removed from the Git index and ignored. The tracked SQLite database was already deleted in the pre-existing working tree; `.gitignore` now excludes local database files.
- **README claims exceeded implementation.** In particular, it described cart/payment/rate-limit behavior that was absent. Documentation now describes the implemented cash-on-delivery API and limitations.

## Notes on scope

The initial settings module reference was not broken in the inspected working tree: `manage.py` and `emarket/settings.py` agree. The old `Ecommerce/` package deletion was already present as a local working-tree change. No user data or Git history was reset or rewritten.
