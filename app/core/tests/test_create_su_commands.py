"""
Tests for create superuser commands
"""
from unittest.mock import patch
from django.core.management import call_command
from django.test import TestCase

import os
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model


class PreCreateCommandTests(TestCase):
    """
    Tests for pre_create_su command
    """
    @patch.dict(os.environ, {
        "SU_EMAIL": "admin@example.com",
        "SU_UID": "google-uid-123"
    })
    def test_creates_new_superuser_with_social_account(self):
        """
        Test that pre-creating a user with social account works
        """
        User = get_user_model()
        email = os.environ["SU_EMAIL"]
        uid = os.environ["SU_UID"]

        call_command("pre_create_su")

        # Check user created
        user = User.objects.get(email=email)
        self.assertEqual(user.email, email)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertFalse(user.has_usable_password())

        # Check social account created
        social_acc = SocialAccount.objects.get(user=user, provider="google")
        self.assertEqual(social_acc.uid, uid)

        # Check email address record
        email_address = EmailAddress.objects.get(user=user, email=email)
        self.assertTrue(email_address.verified)
        self.assertTrue(email_address.primary)
