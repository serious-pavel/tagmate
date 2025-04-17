from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from app.settings import LOGIN_URL

User = get_user_model()


class AuthenticationBackendTest(TestCase):
    """Test cases for authentication backends."""
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='test_pass123',
        )

    def test_user_is_created_correctly(self):
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_authenticate_with_password_fails(self):
        """Ensure password-based login is completely disabled."""
        user = authenticate(email='test@example.com', password='test_pass123')
        self.assertIsNone(user)


class AdminLoginTest(TestCase):
    def test_admin_login_redirects(self):
        """Test redirect from admin login page."""
        response = self.client.get('/admin/login/', follow=True)
        self.assertRedirects(response, f'{LOGIN_URL}?next=/admin/login/')

    def test_non_staff_user_cannot_access_admin(self):
        """Test non-staff user cannot access admin page."""
        user = User.objects.create_user(email="user@example.com")
        self.client.force_login(user)

        response = self.client.get('/admin/', follow=True)
        self.assertEqual(response.status_code, 403)

        user.is_staff = True
        user.save()

        response = self.client.get('/admin/', follow=True)
        self.assertEqual(response.status_code, 200)
