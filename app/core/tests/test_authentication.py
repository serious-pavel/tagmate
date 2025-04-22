from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from app.settings import LOGIN_URL

from allauth.socialaccount.models import SocialAccount, SocialLogin
from core.social_adapters import MySocialAccountAdapter
from django.contrib.sessions.middleware import SessionMiddleware

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


class GoogleLoginTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def add_session_to_request(self, request):
        """Attach a session to the request."""
        middleware = SessionMiddleware(lambda rqst: None)
        middleware.process_request(request)
        request.session.save()

    def test_social_login_creates_user(self):
        adapter = MySocialAccountAdapter()
        request = self.factory.get("/accounts/google/login/callback/")
        self.add_session_to_request(request)

        # Simulate sociallogin object
        sociallogin = SocialLogin()
        sociallogin.account = SocialAccount(
            provider="google",
            uid="google-12345",
            extra_data={
                "email": "socialuser@example.com",
                "name": "Social User",
                "picture": "https://example.com/pic.jpg",
            },
        )
        sociallogin.user = User(email="socialuser@example.com")

        # Populate and save user
        user = adapter.populate_user(
            request,
            sociallogin,
            sociallogin.account.extra_data
        )
        user.set_unusable_password()
        user.save()
        sociallogin.user = user
        sociallogin.save(request)

        # Assertions
        created_user = User.objects.get(email="socialuser@example.com")
        self.assertEqual(created_user.full_name, "Social User")
        self.assertEqual(
            created_user.profile_picture, "https://example.com/pic.jpg"
        )
        self.assertTrue(
            SocialAccount.objects.filter(user=created_user, provider="google").exists()
        )
