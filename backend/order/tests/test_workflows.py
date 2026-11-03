from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

from django.contrib.auth import get_user_model
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from account.models import Address, AuditLog, Notification
from order.models import (
    Cart,
    CartItem,
    Coupon,
    CouponRedemption,
    LoyaltyTransaction,
    LoyaltyWallet,
    Order,
    Payment,
    Refund,
    ReturnRequest,
    ShippingMethod,
    ShippingZone,
)
from order.services import checkout, collect_cod, complete_refund
from product.models import Brand, Category, InventoryMovement, Product, ProductVariant

User = get_user_model()


class CommerceWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("buyer", email="buyer@example.com", password="A-very-strong-passphrase-2026")
        self.staff = User.objects.create_user("staff", password="A-very-strong-passphrase-2026", is_staff=True)
        category = Category.objects.create(name="Home", slug="home")
        brand = Brand.objects.create(name="Alexandria", slug="alexandria")
        product = Product.objects.create(name="Lamp", slug="lamp", description="Lamp", category=category, brand=brand, status=Product.Status.ACTIVE)
        self.variant = ProductVariant.objects.create(product=product, sku="LAMP-01", price=Decimal("100.00"), stock=3)
        self.address = Address.objects.create(
            user=self.user, recipient="Buyer", phone="0100", line1="Main", city="Cairo", state="Cairo", country="EG", is_default=True
        )
        zone = ShippingZone.objects.create(name="Egypt", countries=["EG"])
        self.shipping = ShippingMethod.objects.create(zone=zone, name="Cairo delivery", code="cairo", flat_fee=Decimal("20.00"))
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=self.cart, variant=self.variant, quantity=2)
        LoyaltyWallet.objects.create(user=self.user, available_points=100)
        self.coupon = Coupon.objects.create(
            code="SAVE10",
            kind=Coupon.Kind.PERCENT,
            value=Decimal("10"),
            minimum_subtotal=Decimal("100"),
            valid_from=timezone.now() - timezone.timedelta(days=1),
            valid_to=timezone.now() + timezone.timedelta(days=1),
            total_limit=1,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def checkout(self, key="checkout-1"):
        return self.client.post(
            "/api/v1/checkout/",
            {"address_id": self.address.pk, "shipping_method_id": self.shipping.pk, "coupon_code": "save10", "points": 100},
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
        )

    def test_quote_and_idempotent_checkout_use_exact_server_money(self):
        quote = self.client.post(
            "/api/v1/checkout/preview/",
            {"address_id": self.address.pk, "shipping_method_id": self.shipping.pk, "coupon_code": "SAVE10", "points": 100},
            format="json",
        )
        self.assertEqual(quote.status_code, 200, quote.data)
        self.assertEqual(quote.data["total"], Decimal("190.00"))
        first = self.checkout()
        second = self.checkout()
        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(second.status_code, 200, second.data)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.get()
        self.assertEqual(order.total, Decimal("190.00"))
        self.assertEqual(order.items.get().unit_price, Decimal("100.00"))
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 1)
        self.assertEqual(CouponRedemption.objects.count(), 1)
        self.assertEqual(LoyaltyTransaction.objects.filter(kind=LoyaltyTransaction.Kind.REDEEM).count(), 1)

    def test_idempotency_conflict_and_cancellation_restore_once(self):
        self.assertEqual(self.checkout().status_code, 201)
        conflict = self.client.post(
            "/api/v1/checkout/",
            {"address_id": self.address.pk, "shipping_method_id": self.shipping.pk, "points": 0},
            format="json",
            HTTP_IDEMPOTENCY_KEY="checkout-1",
        )
        self.assertEqual(conflict.status_code, 400)
        order = Order.objects.get()
        self.assertEqual(self.client.post(f"/api/v1/orders/{order.pk}/cancel/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/orders/{order.pk}/cancel/").status_code, 400)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 3)
        self.assertEqual(InventoryMovement.objects.filter(reason=InventoryMovement.Reason.CANCEL).count(), 1)
        self.assertEqual(LoyaltyWallet.objects.get(user=self.user).available_points, 100)
        self.assertIsNotNone(CouponRedemption.objects.get().released_at)

    def test_invalid_coupon_points_and_shipping_fail_without_side_effects(self):
        self.coupon.valid_to = timezone.now() - timezone.timedelta(minutes=1)
        self.coupon.save(update_fields=("valid_to",))
        expired = self.checkout()
        self.assertEqual(expired.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)
        self.coupon.valid_to = timezone.now() + timezone.timedelta(days=1)
        self.coupon.save(update_fields=("valid_to",))
        invalid_points = self.client.post(
            "/api/v1/checkout/",
            {"address_id": self.address.pk, "shipping_method_id": self.shipping.pk, "points": 11},
            format="json",
            HTTP_IDEMPOTENCY_KEY="invalid-points",
        )
        self.assertEqual(invalid_points.status_code, 400)
        self.shipping.zone.countries = ["US"]
        self.shipping.zone.save(update_fields=("countries",))
        unavailable = self.client.post(
            "/api/v1/checkout/preview/",
            {"address_id": self.address.pk, "shipping_method_id": self.shipping.pk},
            format="json",
        )
        self.assertEqual(unavailable.status_code, 400)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 3)

    def test_customer_cannot_see_or_transition_another_customer_order(self):
        self.assertEqual(self.checkout().status_code, 201)
        order = Order.objects.get()
        other = User.objects.create_user("other-buyer", email="other-buyer@example.com", password="A-very-strong-passphrase-2026")
        client = APIClient()
        client.force_authenticate(other)
        self.assertEqual(client.get(f"/api/v1/orders/{order.pk}/").status_code, 404)
        self.assertEqual(client.post(f"/api/v1/orders/{order.pk}/transition/", {"status": "confirmed"}, format="json").status_code, 403)

    def test_empty_cart_checkout_has_no_side_effects(self):
        self.cart.items.all().delete()
        response = self.checkout()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(CouponRedemption.objects.count(), 0)

    def test_staff_manages_coupon_and_shipping_configuration(self):
        customer_response = self.client.post("/api/v1/admin/coupons/", {}, format="json")
        self.assertEqual(customer_response.status_code, 403)
        staff_client = APIClient()
        staff_client.force_authenticate(self.staff)
        invalid = staff_client.post(
            "/api/v1/admin/coupons/",
            {
                "code": "TOO-MUCH",
                "kind": "percent",
                "value": "150.00",
                "valid_from": timezone.now().isoformat(),
                "valid_to": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            },
            format="json",
        )
        self.assertEqual(invalid.status_code, 400)
        valid = staff_client.post(
            "/api/v1/admin/coupons/",
            {
                "code": "STAFF20",
                "kind": "percent",
                "value": "20.00",
                "valid_from": timezone.now().isoformat(),
                "valid_to": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            },
            format="json",
        )
        self.assertEqual(valid.status_code, 201, valid.data)
        zone = staff_client.post(
            "/api/v1/admin/shipping/zones/",
            {"name": "Alexandria", "countries": ["EG"], "states": ["Alexandria"], "is_active": True},
            format="json",
        )
        self.assertEqual(zone.status_code, 201, zone.data)
        method = staff_client.post(
            "/api/v1/admin/shipping/methods/",
            {"zone": zone.data["id"], "name": "Alex express", "code": "alex-express", "flat_fee": "75.00"},
            format="json",
        )
        self.assertEqual(method.status_code, 201, method.data)

    def test_paid_and_delivered_cod_earns_once(self):
        self.assertEqual(self.checkout().status_code, 201)
        order = Order.objects.get()
        staff_client = APIClient()
        staff_client.force_authenticate(self.staff)
        for new_status in (Order.Status.CONFIRMED, Order.Status.SHIPPED):
            self.assertEqual(staff_client.post(f"/api/v1/orders/{order.pk}/transition/", {"status": new_status}, format="json").status_code, 200)
        payment = Payment.objects.get(order=order)
        self.assertEqual(staff_client.post(f"/api/v1/admin/payments/{payment.pk}/collect/").status_code, 200)
        self.assertEqual(staff_client.post(f"/api/v1/orders/{order.pk}/transition/", {"status": Order.Status.DELIVERED}, format="json").status_code, 200)
        self.assertEqual(staff_client.post(f"/api/v1/admin/payments/{payment.pk}/collect/").status_code, 200)
        self.assertEqual(LoyaltyTransaction.objects.filter(kind=LoyaltyTransaction.Kind.EARN).count(), 1)

    def test_review_return_refund_notifications_audit_and_reports(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(self.checkout().status_code, 201)
        order = Order.objects.get()
        staff_client = APIClient()
        staff_client.force_authenticate(self.staff)
        for new_status in (Order.Status.CONFIRMED, Order.Status.SHIPPED):
            response = staff_client.post(f"/api/v1/orders/{order.pk}/transition/", {"status": new_status}, format="json")
            self.assertEqual(response.status_code, 200)
        payment = Payment.objects.get(order=order)
        staff_client.post(f"/api/v1/admin/payments/{payment.pk}/collect/")
        staff_client.post(f"/api/v1/orders/{order.pk}/transition/", {"status": Order.Status.DELIVERED}, format="json")
        product_id = self.variant.product_id
        review = self.client.post(
            f"/api/v1/catalog/products/{product_id}/reviews/",
            {"rating": 5, "comment": "Excellent"},
            format="json",
        )
        self.assertEqual(review.status_code, 201, review.data)
        moderated = staff_client.post(
            f"/api/v1/catalog/products/{product_id}/reviews/{review.data['id']}/moderate/",
            {"is_approved": True},
            format="json",
        )
        self.assertEqual(moderated.status_code, 200, moderated.data)
        public_reviews = APIClient().get(f"/api/v1/catalog/products/{product_id}/reviews/")
        self.assertEqual(public_reviews.data["count"], 1)
        item = order.items.get()
        returned = self.client.post(
            "/api/v1/orders/returns/",
            {"order_item": item.pk, "quantity": 1, "reason": "Changed mind"},
            format="json",
        )
        self.assertEqual(returned.status_code, 201, returned.data)
        decided = staff_client.post(
            f"/api/v1/orders/returns/{returned.data['id']}/decide/",
            {"status": "approved", "staff_note": "Accepted"},
            format="json",
        )
        self.assertEqual(decided.status_code, 200, decided.data)
        refund = Refund.objects.get(return_request_id=returned.data["id"])
        self.assertEqual(refund.status, Refund.Status.PENDING)
        self.assertEqual(staff_client.post(f"/api/v1/admin/refunds/{refund.pk}/complete/").status_code, 200)
        self.assertEqual(staff_client.post(f"/api/v1/admin/refunds/{refund.pk}/complete/").status_code, 200)
        return_request = ReturnRequest.objects.get(pk=returned.data["id"])
        self.assertEqual(return_request.status, ReturnRequest.Status.COMPLETED)
        wallet = LoyaltyWallet.objects.get(user=self.user)
        self.assertEqual(wallet.available_points, 59)
        self.assertEqual(wallet.outstanding_clawback, 0)
        self.assertEqual(return_request.timeline.count(), 3)
        self.assertEqual(staff_client.get("/api/v1/admin/reports/summary/").status_code, 200)
        self.assertTrue(Notification.objects.filter(user=self.user).exists())
        self.assertTrue(AuditLog.objects.filter(actor=self.staff).exists())


class PostgreSQLCheckoutConcurrencyTests(TransactionTestCase):
    @skipUnlessDBFeature("has_select_for_update")
    def test_final_stock_and_coupon_slot_cannot_be_consumed_twice(self):
        category = Category.objects.create(name="Race", slug="race")
        brand = Brand.objects.create(name="Race Brand", slug="race-brand")
        product = Product.objects.create(
            name="Final unit",
            slug="final-unit",
            description="Concurrency fixture",
            category=category,
            brand=brand,
            status=Product.Status.ACTIVE,
        )
        variant = ProductVariant.objects.create(product=product, sku="FINAL-1", price=Decimal("100.00"), stock=1)
        zone = ShippingZone.objects.create(name="Race zone", countries=["EG"])
        shipping = ShippingMethod.objects.create(zone=zone, name="Race shipping", code="race-shipping", flat_fee=0)
        coupon = Coupon.objects.create(
            code="LAST",
            kind=Coupon.Kind.FIXED,
            value=Decimal("10.00"),
            valid_from=timezone.now() - timezone.timedelta(days=1),
            valid_to=timezone.now() + timezone.timedelta(days=1),
            total_limit=1,
        )
        users = []
        for index in range(2):
            user = User.objects.create_user(f"racer-{index}", password="A-very-strong-passphrase-2026")
            address = Address.objects.create(user=user, recipient="Racer", phone="1", line1="x", city="x", state="x")
            cart = Cart.objects.create(user=user)
            CartItem.objects.create(cart=cart, variant=variant, quantity=1)
            users.append((user.pk, address.pk))
        barrier = Barrier(2)

        def race(ids):
            close_old_connections()
            try:
                user = User.objects.get(pk=ids[0])
                address = Address.objects.get(pk=ids[1])
                barrier.wait(timeout=10)
                try:
                    checkout(
                        user=user,
                        address=address,
                        shipping_method_id=shipping.pk,
                        coupon_code=coupon.code,
                        points=0,
                        idempotency_key=f"race-{user.pk}",
                    )
                    return "created"
                except ValidationError:
                    return "rejected"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(race, users))
        self.assertCountEqual(outcomes, ["created", "rejected"])
        variant.refresh_from_db()
        self.assertEqual(variant.stock, 0)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(CouponRedemption.objects.filter(released_at__isnull=True).count(), 1)

    @skipUnlessDBFeature("has_select_for_update")
    def test_same_wallet_and_cart_cannot_be_spent_twice(self):
        category = Category.objects.create(name="Points race", slug="points-race")
        brand = Brand.objects.create(name="Points Brand", slug="points-brand")
        product = Product.objects.create(
            name="Points item",
            slug="points-item",
            description="Concurrency fixture",
            category=category,
            brand=brand,
            status=Product.Status.ACTIVE,
        )
        variant = ProductVariant.objects.create(product=product, sku="POINTS-1", price=Decimal("100.00"), stock=2)
        zone = ShippingZone.objects.create(name="Points zone", countries=["EG"])
        shipping = ShippingMethod.objects.create(zone=zone, name="Points shipping", code="points-shipping", flat_fee=0)
        user = User.objects.create_user("points-racer", email="points-racer@example.com", password="A-very-strong-passphrase-2026")
        address = Address.objects.create(user=user, recipient="Racer", phone="1", line1="x", city="x", state="x", country="EG")
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, variant=variant, quantity=1)
        LoyaltyWallet.objects.create(user=user, available_points=100)
        barrier = Barrier(2)

        def race(key):
            close_old_connections()
            try:
                racer = User.objects.get(pk=user.pk)
                delivery_address = Address.objects.get(pk=address.pk)
                barrier.wait(timeout=10)
                try:
                    checkout(
                        user=racer,
                        address=delivery_address,
                        shipping_method_id=shipping.pk,
                        points=100,
                        idempotency_key=key,
                    )
                    return "created"
                except ValidationError:
                    return "rejected"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(race, ("points-race-a", "points-race-b")))
        self.assertCountEqual(outcomes, ["created", "rejected"])
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(LoyaltyWallet.objects.get(user=user).available_points, 0)
        self.assertEqual(LoyaltyTransaction.objects.filter(kind=LoyaltyTransaction.Kind.REDEEM).count(), 1)

    @skipUnlessDBFeature("has_select_for_update")
    def test_duplicate_payment_and_refund_processing_is_idempotent(self):
        customer = User.objects.create_user("refund-customer", email="refund-customer@example.com", password="A-very-strong-passphrase-2026")
        staff = User.objects.create_user("refund-staff", email="refund-staff@example.com", password="A-very-strong-passphrase-2026", is_staff=True)
        order = Order.objects.create(
            user=customer,
            status=Order.Status.SHIPPED,
            subtotal=Decimal("100.00"),
            shipping_fee=0,
            total=Decimal("100.00"),
            shipping_method_name="Test",
            shipping_address={"country": "EG"},
        )
        payment = Payment.objects.create(order=order, amount=order.total, transaction_reference="COD-CONCURRENT")
        barrier = Barrier(2)

        def collect(_):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return collect_cod(payment=Payment.objects.get(pk=payment.pk), actor=User.objects.get(pk=staff.pk)).status
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            self.assertEqual(list(executor.map(collect, range(2))), [Payment.Status.PAID, Payment.Status.PAID])
        self.assertEqual(AuditLog.objects.filter(action="payment.collect", entity_id=str(payment.pk)).count(), 1)

        category = Category.objects.create(name="Refund", slug="refund")
        brand = Brand.objects.create(name="Refund Brand", slug="refund-brand")
        product = Product.objects.create(
            name="Refund item", slug="refund-item", description="Fixture", category=category, brand=brand, status=Product.Status.ACTIVE
        )
        variant = ProductVariant.objects.create(product=product, sku="REFUND-1", price=Decimal("100.00"), stock=0)
        item = order.items.create(
            variant=variant,
            product_name=product.name,
            sku=variant.sku,
            unit_price=variant.price,
            quantity=1,
            line_total=variant.price,
        )
        returned = ReturnRequest.objects.create(
            order_item=item,
            user=customer,
            quantity=1,
            reason="Fixture",
            status=ReturnRequest.Status.APPROVED,
            refund_amount=Decimal("100.00"),
        )
        refund = Refund.objects.create(return_request=returned, payment=payment, amount=Decimal("100.00"), reference="REF-CONCURRENT")
        refund_barrier = Barrier(2)

        def complete(_):
            close_old_connections()
            try:
                refund_barrier.wait(timeout=10)
                return complete_refund(refund=Refund.objects.get(pk=refund.pk), actor=User.objects.get(pk=staff.pk)).status
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            self.assertEqual(list(executor.map(complete, range(2))), [Refund.Status.COMPLETED, Refund.Status.COMPLETED])
        self.assertEqual(AuditLog.objects.filter(action="refund.complete", entity_id=str(refund.pk)).count(), 1)
