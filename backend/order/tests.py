from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from django.test.utils import CaptureQueriesContext
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from order.models import Cart, CartItem, Order, OrderStatus
from order.services import checkout
from product.models import Category, Products


class CheckoutAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer', password='long-password-123')
        self.product = Products.objects.create(name='Book', description='A book', price=Decimal('12.50'), brand='X', category=Category.HOME, stock=4)
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def address(self):
        return {'city': 'Cairo', 'zip_code': '12345', 'street': 'Main', 'state': '', 'country': 'Egypt', 'phone_no': '123456789'}

    def test_checkout_uses_database_price_and_reduces_stock(self):
        response = self.client.post('/api/orders/new/', {
            **self.address(), 'order_Items': [{'product': self.product.pk, 'quantity': 2, 'price': '0.01'}],
        }, format='json')
        self.assertEqual(response.status_code, 201)
        order = Order.objects.get()
        self.assertEqual(order.total_amount, Decimal('25.00'))
        self.assertEqual(order.orderitems.get().price, Decimal('12.50'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 2)
        self.assertFalse(self.cart.items.exists())


    def test_checkout_rejects_insufficient_stock_without_partial_order(self):
        self.product.stock = 1
        self.product.save(update_fields=['stock'])
        response = self.client.post('/api/orders/new/', self.address(), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)

    def test_checkout_rolls_back_order_and_stock_when_conditional_update_fails(self):
        second = Products.objects.create(name='Pen', description='Pen', price=Decimal('2.00'), brand='X', category=Category.HOME, stock=5)
        CartItem.objects.create(cart=self.cart, product=second, quantity=1)
        from order import services
        real_update = services._decrement_stock
        calls = 0

        def fail_second(product, quantity):
            nonlocal calls
            calls += 1
            return real_update(product, quantity) if calls == 1 else 0

        with patch('order.services._decrement_stock', side_effect=fail_second):
            response = self.client.post('/api/orders/new/', self.address(), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)
        self.product.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(self.product.stock, 4)
        self.assertEqual(second.stock, 5)
        self.assertEqual(self.cart.items.count(), 2)

    def test_order_status_payload_is_validated(self):
        admin = User.objects.create_user(username='admin', password='long-password-123', is_staff=True)
        self.client.force_authenticate(admin)
        order = Order.objects.create(user=self.user, city='C', zip_code='1', street='S', country='E', phone_no='123')
        response = self.client.put(f'/api/order/{order.pk}/process/', {'status': []}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_staff_status_transitions_and_customer_cancellation_boundary(self):
        order = Order.objects.create(user=self.user, city='C', zip_code='1', street='S', country='E', phone_no='123')
        response = self.client.put(f'/api/order/{order.pk}/process/', {'status': 'Shipped'}, format='json')
        self.assertEqual(response.status_code, 403)

        admin = User.objects.create_user(username='status-admin', password='long-password-123', is_staff=True)
        self.client.force_authenticate(admin)
        response = self.client.put(f'/api/order/{order.pk}/process/', {'status': 'Shipped'}, format='json')
        self.assertEqual(response.status_code, 200)

        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.delete(f'/api/order/{order.pk}/delete/').status_code, 400)
        self.client.force_authenticate(admin)
        response = self.client.put(f'/api/order/{order.pk}/process/', {'status': 'Delivered'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.delete(f'/api/order/{order.pk}/delete/').status_code, 400)

    def test_cart_totals_use_current_product_price_and_reject_excess_stock(self):
        response = self.client.get('/api/cart/')
        self.assertEqual(response.data['total'], Decimal('25.00'))
        response = self.client.post('/api/cart/', {'product_id': self.product.pk, 'quantity': 3}, format='json')
        self.assertEqual(response.status_code, 400)
        item = CartItem.objects.get(cart=self.cart, product=self.product)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(CartItem.objects.count(), 1)
        self.product.price = Decimal('15.00')
        self.product.save(update_fields=['price'])
        response = self.client.get('/api/cart/')
        self.assertEqual(response.data['total'], Decimal('30.00'))

    def test_rejected_new_cart_item_does_not_create_cart_or_item(self):
        new_user = User.objects.create_user(username='empty-buyer', password='long-password-123')
        self.client.force_authenticate(new_user)
        before_carts = Cart.objects.count()
        before_items = CartItem.objects.count()

        response = self.client.post(
            '/api/cart/', {'product_id': self.product.pk, 'quantity': self.product.stock + 1}, format='json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Cart.objects.count(), before_carts)
        self.assertEqual(CartItem.objects.count(), before_items)
        self.assertFalse(Cart.objects.filter(user=new_user).exists())

    def test_rejected_cart_item_put_keeps_existing_quantity(self):
        item = self.cart.items.get(product=self.product)

        response = self.client.put(
            f'/api/cart/items/{item.pk}/', {'quantity': self.product.stock + 1}, format='json'
        )

        self.assertEqual(response.status_code, 400)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 2)
        self.assertEqual(CartItem.objects.count(), 1)

    def test_empty_cart_cannot_checkout(self):
        self.cart.items.all().delete()
        response = self.client.post('/api/orders/new/', self.address(), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)


    def test_order_history_is_customer_scoped(self):
        other = User.objects.create_user(username='other', password='long-password-123')
        order = Order.objects.create(user=other, city='C', zip_code='1', street='S', country='E', phone_no='123')
        self.assertEqual(self.client.get('/api/orders/').data['orders'], [])
        self.assertEqual(self.client.get(f'/api/order/{order.pk}/').status_code, 404)
        self.assertEqual(self.client.delete(f'/api/order/{order.pk}/delete/').status_code, 404)


    def test_cancellation_restores_inventory_once(self):
        from order.models import OrderItem
        self.product.stock = 2
        self.product.save(update_fields=['stock'])
        order = Order.objects.create(user=self.user, city='C', zip_code='1', street='S', country='E', phone_no='123')
        OrderItem.objects.create(order=order, product=self.product, name=self.product.name, quantity=2, price=self.product.price)
        self.assertEqual(self.client.delete(f'/api/order/{order.pk}/delete/').status_code, 204)
        self.assertEqual(self.client.delete(f'/api/order/{order.pk}/delete/').status_code, 204)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 4)
        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.CANCELLED)


class CheckoutLockingTests(TransactionTestCase):
    @skipUnlessDBFeature('has_select_for_update')
    def test_checkout_uses_database_row_locks(self):
        user = User.objects.create_user(username='locked-buyer', password='long-password-123')
        product = Products.objects.create(name='Locked book', description='Book', price=Decimal('4.00'), brand='X', category=Category.HOME, stock=1)
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        address = {'city':'Cairo', 'zip_code':'12345', 'street':'Main', 'state':'', 'country':'Egypt', 'phone_no':'123456789'}
        with CaptureQueriesContext(connection) as queries:
            checkout(user=user, address=address)
        self.assertTrue(any('FOR UPDATE' in query['sql'].upper() for query in queries))
        product.refresh_from_db()
        self.assertEqual(product.stock, 0)

    @skipUnlessDBFeature('has_select_for_update')
    def test_concurrent_checkouts_cannot_oversell_the_last_unit(self):
        product = Products.objects.create(
            name='Last book', description='Book', price=Decimal('4.00'),
            brand='X', category=Category.HOME, stock=1,
        )
        buyers = [
            User.objects.create_user(username=f'concurrent-buyer-{index}', password='long-password-123')
            for index in range(2)
        ]
        for buyer in buyers:
            cart = Cart.objects.create(user=buyer)
            CartItem.objects.create(cart=cart, product=product, quantity=1)
        barrier = Barrier(2)
        address = {
            'city': 'Cairo', 'zip_code': '12345', 'street': 'Main',
            'state': '', 'country': 'Egypt', 'phone_no': '123456789',
        }

        def submit_checkout(user_id):
            close_old_connections()
            try:
                buyer = User.objects.get(pk=user_id)
                barrier.wait(timeout=10)
                try:
                    checkout(user=buyer, address=address)
                    return 'created'
                except ValidationError:
                    return 'rejected'
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(submit_checkout, [buyer.pk for buyer in buyers]))

        self.assertCountEqual(outcomes, ['created', 'rejected'])
        product.refresh_from_db()
        self.assertEqual(product.stock, 0)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.get().orderitems.get().quantity, 1)
