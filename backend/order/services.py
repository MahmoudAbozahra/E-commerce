from decimal import Decimal

from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError

from product.models import Products

from .models import Order, OrderItem, OrderStatus


def _decrement_stock(product, quantity):
    return Products.objects.filter(pk=product.pk, stock__gte=quantity).update(stock=F("stock") - quantity)


@transaction.atomic
def checkout(*, user, address: dict) -> Order:
    """Create an order using current database prices and reserve stock atomically."""
    from .models import Cart

    cart = Cart.objects.select_for_update().filter(user=user).first()
    if not cart or not cart.items.exists():
        raise ValidationError({"cart": "Your cart is empty."})
    cart_items = list(cart.items.select_for_update().order_by("product_id"))
    product_ids = [item.product_id for item in cart_items]
    locked_products = {p.pk: p for p in Products.objects.select_for_update().filter(pk__in=product_ids).order_by("pk")}
    if len(locked_products) != len(set(product_ids)):
        raise ValidationError({"cart": "A product in your cart is no longer available."})

    total = Decimal("0.00")
    lines = []
    for cart_item in cart_items:
        product = locked_products[cart_item.product_id]
        if cart_item.quantity < 1:
            raise ValidationError({"quantity": "Quantity must be positive."})
        if product.stock < cart_item.quantity:
            raise ValidationError({"stock": f"Insufficient stock for {product.name}."})
        total += product.price * cart_item.quantity
        lines.append((product, cart_item.quantity, product.price))

    order = Order.objects.create(user=user, total_amount=total, payment_method="cod", **address)
    OrderItem.objects.bulk_create(
        [OrderItem(order=order, product=product, name=product.name, quantity=quantity, price=price) for product, quantity, price in lines]
    )
    for product, quantity, _ in lines:
        updated = _decrement_stock(product, quantity)
        if updated != 1:
            raise ValidationError({"stock": f"Insufficient stock for {product.name}."})
    cart.items.all().delete()
    return order


@transaction.atomic
def transition_order(*, order: Order, new_status: str) -> Order:
    order = Order.objects.select_for_update().get(pk=order.pk)
    allowed = {
        OrderStatus.PROCESSING: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
        OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
        OrderStatus.DELIVERED: set(),
        OrderStatus.CANCELLED: set(),
    }
    if new_status not in OrderStatus.values or new_status not in allowed.get(order.status, set()):
        raise ValidationError({"status": "Invalid order status transition."})
    if new_status == OrderStatus.CANCELLED:
        items = order.orderitems.select_related("product").all()
        for item in items:
            if item.product_id:
                Products.objects.filter(pk=item.product_id).update(stock=F("stock") + item.quantity)
    order.status = new_status
    order.save(update_fields=["status"])
    return order
