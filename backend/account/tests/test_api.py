from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.test import APIClient

from account.models import Address

User = get_user_model()


class AccountAPITests(TestCase):
    def test_registration_login_profile_and_address_ownership(self):
        client = APIClient()
        payload = {"username": "sara", "email": "SARA@example.com", "first_name": "Sara", "last_name": "Ali", "password": "A-very-strong-passphrase-2026"}
        self.assertEqual(client.post("/api/v1/auth/register/", payload, format="json").status_code, 201)
        self.assertEqual(User.objects.get(username="sara").email, "sara@example.com")
        tokens = client.post("/api/v1/auth/login/", {"username": "sara", "password": payload["password"]}, format="json")
        self.assertEqual(tokens.status_code, 200)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens.data['access']}")
        address = client.post(
            "/api/v1/users/addresses/",
            {"recipient": "Sara Ali", "phone": "+201000000000", "line1": "10 Nile St", "city": "Cairo", "state": "Cairo", "country": "EG"},
            format="json",
        )
        self.assertEqual(address.status_code, 201, address.data)
        self.assertTrue(Address.objects.get(pk=address.data["id"]).is_default)
        other = User.objects.create_user("other", password="A-very-strong-passphrase-2026")
        foreign = Address.objects.create(user=other, recipient="Other", phone="1", line1="x", city="x", state="x")
        self.assertEqual(client.get(f"/api/v1/users/addresses/{foreign.pk}/").status_code, 404)

    def test_duplicate_email_is_case_insensitive_and_roles_are_not_assignable(self):
        User.objects.create_user("existing", email="buyer@example.com", password="A-very-strong-passphrase-2026")
        response = APIClient().post(
            "/api/v1/auth/register/",
            {"username": "new", "email": "BUYER@example.com", "password": "A-very-strong-passphrase-2026", "is_staff": True},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username="new").exists())

    def test_password_change_requires_current_password(self):
        user = User.objects.create_user("password-user", email="password@example.com", password="Old-strong-password-2026")
        client = APIClient()
        client.force_authenticate(user)
        rejected = client.post(
            "/api/v1/auth/password/change/",
            {"current_password": "wrong", "new_password": "New-strong-password-2026"},
            format="json",
        )
        self.assertEqual(rejected.status_code, 400)
        accepted = client.post(
            "/api/v1/auth/password/change/",
            {"current_password": "Old-strong-password-2026", "new_password": "New-strong-password-2026"},
            format="json",
        )
        self.assertEqual(accepted.status_code, 204)
        user.refresh_from_db()
        self.assertTrue(user.check_password("New-strong-password-2026"))

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_request_does_not_enumerate_users(self):
        User.objects.create_user("reset-user", email="reset@example.com", password="Old-strong-password-2026")
        client = APIClient()
        known = client.post("/api/v1/auth/password/reset/request/", {"email": "reset@example.com"}, format="json")
        unknown = client.post("/api/v1/auth/password/reset/request/", {"email": "missing@example.com"}, format="json")
        self.assertEqual(known.status_code, 200)
        self.assertEqual(known.data, unknown.data)
        self.assertEqual(len(mail.outbox), 1)

    def test_only_one_default_address_is_kept(self):
        user = User.objects.create_user("address-user", email="address@example.com", password="A-very-strong-passphrase-2026")
        client = APIClient()
        client.force_authenticate(user)
        payload = {"recipient": "User", "phone": "0100", "line1": "Street", "city": "Cairo", "state": "Cairo", "country": "EG"}
        first = client.post("/api/v1/users/addresses/", payload, format="json")
        second = client.post("/api/v1/users/addresses/", {**payload, "line1": "Other", "is_default": True}, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(Address.objects.filter(user=user, is_default=True).count(), 1)
        self.assertEqual(Address.objects.get(user=user, is_default=True).pk, second.data["id"])

    def test_audit_log_api_is_staff_only(self):
        customer = User.objects.create_user("audit-customer", email="audit-customer@example.com", password="A-very-strong-passphrase-2026")
        staff = User.objects.create_user("audit-staff", email="audit-staff@example.com", password="A-very-strong-passphrase-2026", is_staff=True)
        client = APIClient()
        client.force_authenticate(customer)
        self.assertEqual(client.get("/api/v1/admin/audit-logs/").status_code, 403)
        client.force_authenticate(staff)
        self.assertEqual(client.get("/api/v1/admin/audit-logs/").status_code, 200)
