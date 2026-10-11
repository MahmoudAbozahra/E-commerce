from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from product.models import Category, Products, Review


class ProductAPITests(TestCase):
    def test_product_listing_is_public_and_paginated(self):
        Products.objects.create(name='Phone', description='Phone', price=Decimal('5'), brand='A', category=Category.PHONES, stock=1)
        response = APIClient().get('/api/products/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)


    def test_only_admin_can_modify_products_and_cannot_set_rating(self):
        user = User.objects.create_user(username='customer', password='long-password-123')
        admin = User.objects.create_user(username='admin', password='long-password-123', is_staff=True)
        client = APIClient()
        client.force_authenticate(user)
        payload = {'name':'Phone', 'description':'Phone', 'price':'5.00', 'brand':'A', 'category':'Phones', 'stock':1}
        self.assertEqual(client.post('/api/new_product/', payload, format='json').status_code, 403)
        client.force_authenticate(admin)
        response = client.post('/api/new_product/', {**payload, 'rating':'5'}, format='json')
        self.assertEqual(response.status_code, 201)
        product = Products.objects.get()
        self.assertEqual(product.rating, Decimal('0'))


    def test_review_rating_boundaries(self):
        user = User.objects.create_user(username='reviewer', password='long-password-123')
        product = Products.objects.create(name='Phone', description='Phone', price=Decimal('5'), brand='A', category=Category.PHONES)
        client = APIClient()
        client.force_authenticate(user)
        for rating, expected in ((1, 201), (5, 200), (0, 400), (6, 400)):
            response = client.post(f'/api/{product.pk}/review/', {'rating': rating, 'comment': 'Good'}, format='json')
            self.assertEqual(response.status_code, expected, response.data)
        self.assertEqual(Review.objects.count(), 1)
