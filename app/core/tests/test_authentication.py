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
            is_active=True
        )

    def test_authenticate_with_password_fails(self):
        """Ensure password-based login is completely disabled."""
        user = authenticate(email='test@example.com', password='test_pass123')
        self.assertIsNone(user)
