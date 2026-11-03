import hashlib
import json
import uuid
from decimal import ROUND_DOWN, Decimal

from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from account.models import AuditLog, Notification
from product.models import InventoryMovement, ProductVariant

from .models import (
    Cart,
    CheckoutAttempt,
    Coupon,
    CouponRedemption,
    LoyaltyTransaction,
    LoyaltyWallet,
    Order,
    OrderItem,
    OrderStatusHistory,
    Payment,
    Refund,
    ReturnRequest,
    ReturnStatusHistory,
    ShippingMethod,
)

CENT = Decimal("0.01")


def money(value):
    return Decimal(value).quantize(CENT)


def _notify_after_commit(user_id, kind, title, message, reference=""):
    transaction.on_commit(lambda: Notification.objects.create(user_id=user_id, kind=kind, title=title, message=message, reference=reference))


def _coupon_discount(coupon, items, subtotal, user=None):
    now = timezone.now()
    if not coupon.is_active or not (coupon.valid_from <= now <= coupon.valid_to):
        raise ValidationError({"coupon_code": "Coupon is inactive or expired."})
    eligible_product_ids = set(coupon.products.values_list("id", flat=True))
    eligible_category_ids = set(coupon.categories.values_list("id", flat=True))
    if eligible_product_ids or eligible_category_ids:
        eligible = sum((v.price * q for v, q in items if v.product_id in eligible_product_ids or v.product.category_id in eligible_category_ids), Decimal("0"))
    else:
        eligible = subtotal
    eligible = money(eligible)
    if eligible < coupon.minimum_subtotal:
        raise ValidationError({"coupon_code": "Minimum eligible subtotal was not reached."})
    if user is not None:
        active = coupon.redemptions.filter(released_at__isnull=True)
        if coupon.total_limit is not None and active.count() >= coupon.total_limit:
            raise ValidationError({"coupon_code": "Coupon usage limit was reached."})
        if active.filter(user=user).count() >= coupon.per_user_limit:
            raise ValidationError({"coupon_code": "Your coupon usage limit was reached."})
    if coupon.kind == Coupon.Kind.FIXED:
        discount = coupon.value
    else:
        discount = eligible * coupon.value / Decimal("100")
        if coupon.max_discount is not None:
            discount = min(discount, coupon.max_discount)
    return money(min(discount, eligible))


def calculate_quote(*, user, address, shipping_method_id, coupon_code="", points=0, lock=False):
    cart_qs = Cart.objects.select_for_update() if lock else Cart.objects
    cart = cart_qs.filter(user=user).first()
    if not cart:
        raise ValidationError({"cart": "Your cart is empty."})
    item_qs = cart.items.select_related("variant__product__category").order_by("variant_id")
    if lock:
        item_qs = item_qs.select_for_update()
    cart_items = list(item_qs)
    if not cart_items:
        raise ValidationError({"cart": "Your cart is empty."})
    variant_ids = [item.variant_id for item in cart_items]
    variants_qs = ProductVariant.objects.select_related("product__category").filter(pk__in=variant_ids).order_by("pk")
    if lock:
        variants_qs = variants_qs.select_for_update()
    variants = {variant.pk: variant for variant in variants_qs}
    lines = []
    for item in cart_items:
        variant = variants.get(item.variant_id)
        if not variant or not variant.is_active or variant.product.status != variant.product.Status.ACTIVE:
            raise ValidationError({"cart": f"SKU {item.variant_id} is unavailable."})
        if item.quantity > variant.stock:
            raise ValidationError({"stock": f"Insufficient stock for {variant.sku}."})
        lines.append((variant, item.quantity))
    subtotal = money(sum((variant.price * quantity for variant, quantity in lines), Decimal("0")))
    shipping_qs = ShippingMethod.objects.select_related("zone")
    if lock:
        shipping_qs = shipping_qs.select_for_update()
    shipping = shipping_qs.filter(pk=shipping_method_id, is_active=True, zone__is_active=True).first()
    if not shipping:
        raise ValidationError({"shipping_method_id": "Shipping method is unavailable."})
    countries = {country.upper() for country in shipping.zone.countries}
    states = {state.casefold() for state in shipping.zone.states}
    if countries and address.country.upper() not in countries:
        raise ValidationError({"shipping_method_id": "Shipping method does not serve this country."})
    if states and address.state.casefold() not in states:
        raise ValidationError({"shipping_method_id": "Shipping method does not serve this state."})
    coupon = None
    coupon_discount = Decimal("0.00")
    if coupon_code:
        coupon_qs = Coupon.objects
        if lock:
            coupon_qs = coupon_qs.select_for_update()
        coupon = coupon_qs.filter(code__iexact=coupon_code.strip()).first()
        if not coupon:
            raise ValidationError({"coupon_code": "Invalid coupon."})
        coupon_discount = _coupon_discount(coupon, lines, subtotal, user if lock else None)
    points = int(points or 0)
    if points < 0 or points % 10:
        raise ValidationError({"points": "Points must be a non-negative multiple of 10."})
    wallet_qs = LoyaltyWallet.objects
    wallet, _ = wallet_qs.get_or_create(user=user)
    if lock:
        wallet = LoyaltyWallet.objects.select_for_update().get(pk=wallet.pk)
    if points > wallet.available_points:
        raise ValidationError({"points": "Insufficient loyalty points."})
    remaining = subtotal - coupon_discount
    max_points = int((remaining * Decimal("10")).to_integral_value(rounding=ROUND_DOWN))
    if points > max_points:
        raise ValidationError({"points": "Redemption exceeds eligible merchandise amount."})
    points_discount = money(Decimal(points) / Decimal("10"))
    total = money(remaining - points_discount + shipping.flat_fee)
    return {
        "lines": lines,
        "shipping": shipping,
        "coupon": coupon,
        "subtotal": subtotal,
        "coupon_discount": coupon_discount,
        "points": points,
        "points_discount": points_discount,
        "shipping_fee": money(shipping.flat_fee),
        "tax": Decimal("0.00"),
        "total": total,
        "currency": "EGP",
        "wallet": wallet,
    }


@transaction.atomic
def checkout(*, user, address, shipping_method_id, idempotency_key, coupon_code="", points=0):
    if not idempotency_key or len(idempotency_key) > 100:
        raise ValidationError({"idempotency_key": "A key of at most 100 characters is required."})
    user.__class__.objects.select_for_update().get(pk=user.pk)
    payload = {"address_id": address.pk, "shipping_method_id": shipping_method_id, "coupon_code": coupon_code.strip().upper(), "points": int(points or 0)}
    request_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    attempt = CheckoutAttempt.objects.select_for_update().filter(user=user, key=idempotency_key).select_related("order").first()
    if attempt:
        if attempt.request_hash != request_hash:
            raise ValidationError({"idempotency_key": "This key was already used with a different request."}, code="conflict")
        if attempt.order:
            return attempt.order, False
    else:
        attempt = CheckoutAttempt.objects.create(user=user, key=idempotency_key, request_hash=request_hash)
    quote = calculate_quote(user=user, address=address, shipping_method_id=shipping_method_id, coupon_code=coupon_code, points=points, lock=True)
    snapshot = {
        "recipient": address.recipient,
        "phone": address.phone,
        "line1": address.line1,
        "line2": address.line2,
        "city": address.city,
        "state": address.state,
        "postal_code": address.postal_code,
        "country": address.country,
    }
    order = Order.objects.create(
        user=user,
        coupon=quote["coupon"],
        shipping_method=quote["shipping"],
        shipping_method_name=quote["shipping"].name,
        shipping_address=snapshot,
        subtotal=quote["subtotal"],
        coupon_discount=quote["coupon_discount"],
        points_discount=quote["points_discount"],
        shipping_fee=quote["shipping_fee"],
        tax=quote["tax"],
        total=quote["total"],
        points_redeemed=quote["points"],
    )
    for variant, quantity in quote["lines"]:
        OrderItem.objects.create(
            order=order,
            variant=variant,
            product_name=variant.product.name,
            sku=variant.sku,
            option_values=variant.option_values,
            unit_price=variant.price,
            quantity=quantity,
            line_total=money(variant.price * quantity),
        )
        variant.stock -= quantity
        variant.save(update_fields=("stock", "updated_at"))
        InventoryMovement.objects.create(variant=variant, delta=-quantity, reason=InventoryMovement.Reason.ORDER, actor=user, reference=order.reference)
    if quote["coupon"]:
        CouponRedemption.objects.create(coupon=quote["coupon"], user=user, order=order, amount=quote["coupon_discount"])
    if quote["points"]:
        wallet = quote["wallet"]
        wallet.available_points -= quote["points"]
        wallet.save(update_fields=("available_points", "updated_at"))
        LoyaltyTransaction.objects.create(
            wallet=wallet, delta=-quote["points"], kind=LoyaltyTransaction.Kind.REDEEM, event_key=f"order:{order.pk}:redeem", order=order
        )
    Payment.objects.create(order=order, amount=order.total, transaction_reference=f"COD-{order.reference}")
    OrderStatusHistory.objects.create(order=order, new_status=order.status, actor=user, note="Order created")
    Cart.objects.get(user=user).items.all().delete()
    attempt.order = order
    attempt.save(update_fields=("order",))
    _notify_after_commit(user.pk, "order_created", "Order created", f"Order {order.reference} was created.", order.reference)
    return order, True


@transaction.atomic
def transition_order(*, order, new_status, actor, note=""):
    order = Order.objects.select_for_update().get(pk=order.pk)
    allowed = {
        Order.Status.PENDING: {Order.Status.CONFIRMED, Order.Status.CANCELLED},
        Order.Status.CONFIRMED: {Order.Status.SHIPPED, Order.Status.CANCELLED},
        Order.Status.SHIPPED: {Order.Status.DELIVERED},
        Order.Status.DELIVERED: {Order.Status.RETURNED},
    }
    if new_status not in allowed.get(order.status, set()):
        raise ValidationError({"status": "Invalid order status transition."})
    previous = order.status
    if new_status == Order.Status.CANCELLED:
        _reverse_order(order, actor)
    order.status = new_status
    order.save(update_fields=("status", "updated_at"))
    OrderStatusHistory.objects.create(order=order, previous_status=previous, new_status=new_status, actor=actor, note=note)
    AuditLog.objects.create(actor=actor, action="order.transition", entity_type="order", entity_id=str(order.pk), details={"from": previous, "to": new_status})
    _notify_after_commit(order.user_id, "order_status", "Order updated", f"Order {order.reference} is now {new_status}.", order.reference)
    if new_status == Order.Status.DELIVERED:
        _earn_if_eligible(order)
    return order


def _reverse_order(order, actor):
    if not order.inventory_restored:
        for item in order.items.select_related("variant").order_by("variant_id"):
            if item.variant_id:
                ProductVariant.objects.filter(pk=item.variant_id).update(stock=F("stock") + item.quantity)
                InventoryMovement.objects.create(
                    variant_id=item.variant_id, delta=item.quantity, reason=InventoryMovement.Reason.CANCEL, actor=actor, reference=order.reference
                )
        order.inventory_restored = True
    if order.points_redeemed:
        wallet = LoyaltyWallet.objects.select_for_update().get(user=order.user)
        key = f"order:{order.pk}:redeem-reversal"
        if not LoyaltyTransaction.objects.filter(event_key=key).exists():
            wallet.available_points += order.points_redeemed
            wallet.save(update_fields=("available_points", "updated_at"))
            LoyaltyTransaction.objects.create(wallet=wallet, delta=order.points_redeemed, kind=LoyaltyTransaction.Kind.REVERSE, event_key=key, order=order)
    redemption = CouponRedemption.objects.filter(order=order, released_at__isnull=True).first()
    if redemption:
        redemption.released_at = timezone.now()
        redemption.save(update_fields=("released_at",))
        order.coupon_released = True
    order.save(update_fields=("inventory_restored", "coupon_released", "updated_at"))


def _earn_if_eligible(order):
    payment = order.payments.filter(status=Payment.Status.PAID).first()
    if not payment or order.status != Order.Status.DELIVERED or not order.user_id:
        return
    wallet, _ = LoyaltyWallet.objects.get_or_create(user_id=order.user_id)
    wallet = LoyaltyWallet.objects.select_for_update().get(pk=wallet.pk)
    event_key = f"order:{order.pk}:earn"
    if LoyaltyTransaction.objects.filter(event_key=event_key).exists():
        return
    eligible = max(Decimal("0"), order.subtotal - order.coupon_discount - order.points_discount)
    earned_points = int((eligible / Decimal("10")).to_integral_value(rounding=ROUND_DOWN))
    debt_paid = min(wallet.outstanding_clawback, earned_points)
    available_points = earned_points - debt_paid
    wallet.outstanding_clawback -= debt_paid
    wallet.available_points += available_points
    wallet.save(update_fields=("available_points", "outstanding_clawback", "updated_at"))
    LoyaltyTransaction.objects.create(
        wallet=wallet,
        delta=available_points,
        kind=LoyaltyTransaction.Kind.EARN,
        event_key=event_key,
        order=order,
        metadata={"earned_points": earned_points, "outstanding_clawback_paid": debt_paid},
    )
    _notify_after_commit(order.user_id, "points_earned", "Points earned", f"You earned {available_points} available points.", order.reference)


@transaction.atomic
def collect_cod(*, payment, actor):
    payment = Payment.objects.select_for_update().select_related("order").get(pk=payment.pk)
    if payment.method != Payment.Method.COD:
        raise ValidationError({"payment": "Only COD collection is implemented."})
    if payment.status == Payment.Status.PAID:
        return payment
    if payment.order.status not in {Order.Status.SHIPPED, Order.Status.DELIVERED}:
        raise ValidationError({"order": "COD can be collected only for shipped or delivered orders."})
    payment.status = Payment.Status.PAID
    payment.collected_at = timezone.now()
    payment.save(update_fields=("status", "collected_at", "updated_at"))
    AuditLog.objects.create(actor=actor, action="payment.collect", entity_type="payment", entity_id=str(payment.pk), details={"order": payment.order.reference})
    _earn_if_eligible(payment.order)
    return payment


@transaction.atomic
def create_return_request(*, user, order_item, quantity, reason):
    returned = ReturnRequest.objects.create(user=user, order_item=order_item, quantity=quantity, reason=reason)
    ReturnStatusHistory.objects.create(return_request=returned, new_status=returned.status, actor=user, note="Return requested")
    return returned


def _apply_return_loyalty(*, returned: ReturnRequest, actor) -> None:
    order = returned.order_item.order
    if not order.user_id or not order.subtotal:
        return
    wallet, _ = LoyaltyWallet.objects.get_or_create(user_id=order.user_id)
    wallet = LoyaltyWallet.objects.select_for_update().get(pk=wallet.pk)
    gross_return = returned.order_item.unit_price * returned.quantity
    ratio = min(Decimal("1"), gross_return / order.subtotal)

    redeemed_points = int((Decimal(order.points_redeemed) * ratio).to_integral_value(rounding=ROUND_DOWN))
    redeem_key = f"return:{returned.pk}:redeem-reversal"
    if redeemed_points and not LoyaltyTransaction.objects.filter(event_key=redeem_key).exists():
        wallet.available_points += redeemed_points
        LoyaltyTransaction.objects.create(
            wallet=wallet,
            delta=redeemed_points,
            kind=LoyaltyTransaction.Kind.REVERSE,
            event_key=redeem_key,
            order=order,
            metadata={"return_id": returned.pk, "reason": "returned redeemed points"},
        )

    earned = LoyaltyTransaction.objects.filter(order=order, kind=LoyaltyTransaction.Kind.EARN).first()
    clawback = int((Decimal(earned.delta) * ratio).to_integral_value(rounding=ROUND_DOWN)) if earned else 0
    earn_key = f"return:{returned.pk}:earn-clawback"
    if clawback and not LoyaltyTransaction.objects.filter(event_key=earn_key).exists():
        removed = min(wallet.available_points, clawback)
        wallet.available_points -= removed
        debt = clawback - removed
        wallet.outstanding_clawback += debt
        LoyaltyTransaction.objects.create(
            wallet=wallet,
            delta=-removed,
            kind=LoyaltyTransaction.Kind.REVERSE,
            event_key=earn_key,
            order=order,
            metadata={"return_id": returned.pk, "earned_clawback": clawback, "outstanding_clawback_added": debt},
        )
    wallet.save(update_fields=("available_points", "outstanding_clawback", "updated_at"))
    _notify_after_commit(order.user_id, "return_loyalty", "Loyalty updated", f"Loyalty was adjusted for return {returned.pk}.", order.reference)


@transaction.atomic
def decide_return(*, returned: ReturnRequest, decision: str, actor, note: str = "") -> ReturnRequest:
    returned = ReturnRequest.objects.select_for_update().select_related("order_item__variant", "order_item__order").get(pk=returned.pk)
    if returned.status != ReturnRequest.Status.REQUESTED:
        raise ValidationError({"status": "Return was already decided."})
    previous = returned.status
    returned.status = decision
    returned.staff_note = note
    if decision == ReturnRequest.Status.APPROVED:
        item = returned.order_item
        if item.variant_id:
            ProductVariant.objects.filter(pk=item.variant_id).update(stock=F("stock") + returned.quantity)
            InventoryMovement.objects.create(
                variant_id=item.variant_id,
                delta=returned.quantity,
                reason=InventoryMovement.Reason.RETURN,
                actor=actor,
                reference=f"return:{returned.pk}",
            )
            returned.inventory_restored = True
        order = item.order
        merchandise_paid = max(Decimal("0.00"), order.subtotal - order.coupon_discount - order.points_discount)
        share = (item.unit_price * returned.quantity) / order.subtotal
        returned.refund_amount = money(merchandise_paid * share)
        payment = order.payments.get(method=Payment.Method.COD)
        Refund.objects.create(
            return_request=returned,
            payment=payment,
            amount=returned.refund_amount,
            reference=f"REF-{returned.pk}-{payment.pk}",
        )
        _apply_return_loyalty(returned=returned, actor=actor)
    returned.save()
    ReturnStatusHistory.objects.create(return_request=returned, previous_status=previous, new_status=decision, actor=actor, note=note)
    AuditLog.objects.create(actor=actor, action="return.decide", entity_type="return", entity_id=str(returned.pk), details={"status": decision})
    return returned


@transaction.atomic
def complete_refund(*, refund: Refund, actor) -> Refund:
    refund = Refund.objects.select_for_update().select_related("payment", "return_request").get(pk=refund.pk)
    if refund.status == Refund.Status.COMPLETED:
        return refund
    if refund.status != Refund.Status.PENDING:
        raise ValidationError({"status": "Only pending cash refunds can be completed."})
    refund.status = Refund.Status.COMPLETED
    refund.completed_at = timezone.now()
    refund.save(update_fields=("status", "completed_at"))
    payment = refund.payment
    total_refunded = payment.refunds.filter(status=Refund.Status.COMPLETED).aggregate(value=Sum("amount"))["value"] or Decimal("0")
    payment.status = Payment.Status.REFUNDED if total_refunded >= payment.amount else Payment.Status.PARTIALLY_REFUNDED
    payment.save(update_fields=("status", "updated_at"))
    returned = refund.return_request
    previous = returned.status
    returned.status = ReturnRequest.Status.COMPLETED
    returned.save(update_fields=("status", "updated_at"))
    ReturnStatusHistory.objects.create(
        return_request=returned,
        previous_status=previous,
        new_status=returned.status,
        actor=actor,
        note="Cash refund completed",
    )
    AuditLog.objects.create(actor=actor, action="refund.complete", entity_type="refund", entity_id=str(refund.pk), details={"amount": str(refund.amount)})
    return refund


@transaction.atomic
def adjust_loyalty(*, user, delta: int, actor, reason: str) -> LoyaltyTransaction:
    wallet, _ = LoyaltyWallet.objects.get_or_create(user=user)
    wallet = LoyaltyWallet.objects.select_for_update().get(pk=wallet.pk)
    if not delta or wallet.available_points + delta < 0:
        raise ValidationError({"delta": "Adjustment must be non-zero and cannot make the balance negative."})
    wallet.available_points += delta
    wallet.save(update_fields=("available_points", "updated_at"))
    event = LoyaltyTransaction.objects.create(
        wallet=wallet,
        delta=delta,
        kind=LoyaltyTransaction.Kind.ADJUST,
        event_key=f"staff:{actor.pk}:{uuid.uuid4().hex}",
        metadata={"reason": reason},
    )
    AuditLog.objects.create(
        actor=actor,
        action="loyalty.adjust",
        entity_type="user",
        entity_id=str(user.pk),
        details={"delta": delta, "reason": reason},
    )
    return event
