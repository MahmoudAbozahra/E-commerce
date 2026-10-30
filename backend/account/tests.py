from datetime import timedelta

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from rest_framework.test import APIClient


class AccountAPITests(TestCase):
    def test_jwt_login_and_current_profile(self):
        user = User.objects.create_user(username='token-user', password='original-password-123')
        response = APIClient().post('/api/token/', {'username': user.username, 'password': 'original-password-123'}, format='json')
        self.assertEqual(response.status_code, 200)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        self.assertEqual(client.get('/api/userinfo/').data['username'], user.username)

    def test_registration_hashes_password_and_duplicate_email_is_rejected(self):
        client = APIClient()
        payload = {'first_name':'A', 'last_name':'B', 'username':'person', 'email':'person@example.com', 'password':'Strong-pass-123'}
        response = client.post('/api/register/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username='person')
        self.assertTrue(user.check_password(payload['password']))
        payload['username'] = 'other'
        self.assertEqual(client.post('/api/register/', payload, format='json').status_code, 400)


    def test_user_can_update_profile_without_changing_password_or_role(self):
        user = User.objects.create_user(username='person', password='original-password-123')
        client = APIClient()
        client.force_authenticate(user)
        response = client.put('/api/userinfo/update/', {'first_name':'Updated', 'is_staff':True}, format='json')
        user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.first_name, 'Updated')
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password('original-password-123'))

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset_response_does_not_reveal_account_existence(self):
        User.objects.create_user(username='person', email='person@example.com', password='original-password-123')
        client = APIClient()
        known = client.post('/api/forget_password/', {'email': 'person@example.com'}, format='json')
        unknown = client.post('/api/forget_password/', {'email': 'nobody@example.com'}, format='json')
        self.assertEqual(known.status_code, 200)
        self.assertEqual(known.data, unknown.data)
        self.assertEqual(len(mail.outbox), 1)

    def test_password_reset_is_single_use_and_sets_hashed_password(self):
        user = User.objects.create_user(username='person', email='person@example.com', password='original-password-123')
        user.profile.reset_password_token = 'one-time-token'
        user.profile.reset_password_expire = timezone.now() + timedelta(minutes=30)
        user.profile.save()
        response = APIClient().post('/api/reset_password/one-time-token', {
            'password': 'Brand-New-Not-Related-4421',
            'confirmPassword': 'Brand-New-Not-Related-4421',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password('Brand-New-Not-Related-4421'))
        self.assertEqual(user.profile.reset_password_token, '')
        self.assertEqual(APIClient().post('/api/reset_password/one-time-token', {
            'password': 'Another-New-Password-4321',
            'confirmPassword': 'Another-New-Password-4321',
        }, format='json').status_code, 404)
