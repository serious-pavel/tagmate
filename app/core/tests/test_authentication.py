from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

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
