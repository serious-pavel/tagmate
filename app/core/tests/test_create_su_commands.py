"""
Tests for create superuser commands
"""
from unittest.mock import patch
from django.core.management import call_command
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

import os
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model

SU_EMAIL = 'admin@example.com'
SU_UID = 'google-uid-123'


class PreCreateCommandTests(TestCase):
    """Tests for pre_create_su command"""
    @patch.dict(os.environ, {'SU_EMAIL': SU_EMAIL, 'SU_UID': SU_UID})
    def test_creates_new_superuser_with_social_account(self):
        """
        Test that pre-creating a user with social account works
        """
        User = get_user_model()

        call_command('pre_create_su')

        # Check user created
        user = User.objects.get(email=SU_EMAIL)
        self.assertEqual(user.email, SU_EMAIL)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertFalse(user.has_usable_password())

        # Check social account created
        social_acc = SocialAccount.objects.get(user=user, provider='google')
        self.assertEqual(social_acc.uid, SU_UID)

        # Check email address record
        email_address = EmailAddress.objects.get(user=user, email=SU_EMAIL)
        self.assertTrue(email_address.verified)
        self.assertTrue(email_address.primary)

    @patch.dict(os.environ, {'SU_EMAIL': SU_EMAIL, 'SU_UID': SU_UID})
    def test_existing_user_is_updated(self):
        """
        Test updating an existing user
        """
        User = get_user_model()
        user = User.objects.create(email=SU_EMAIL, password='generic_pass')
        self.assertTrue(user.has_usable_password())

        call_command('pre_create_su')

        user.refresh_from_db()
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertFalse(user.has_usable_password())

    @patch.dict(os.environ, {'SU_EMAIL': SU_EMAIL, 'SU_UID': SU_UID})
    def test_other_social_account_is_retained(self):
        """Test that other linked social accounts are not changed"""
        other_social_uid = 'other-google-uid'
        User = get_user_model()
        user = User.objects.create(email=SU_EMAIL)
        SocialAccount.objects.create(
            user=user,
            provider='google',
            uid=other_social_uid
        )

        self.assertEqual(SocialAccount.objects.filter(user=user).count(), 1)

        call_command('pre_create_su')

        self.assertEqual(SocialAccount.objects.filter(user=user).count(), 2)

    @patch.dict(os.environ, {'SU_EMAIL': SU_EMAIL, 'SU_UID': SU_UID})
    def test_other_email_address_is_retained(self):
        """Test that other linked email addresses are not changed"""
        other_email = 'other@example.com'
        User = get_user_model()
        user = User.objects.create(email=SU_EMAIL)
        EmailAddress.objects.create(user=user, email=other_email)

        self.assertEqual(EmailAddress.objects.filter(user=user).count(), 1)

        call_command('pre_create_su')

        self.assertEqual(EmailAddress.objects.filter(user=user).count(), 2)

    @patch.dict(os.environ, {'SU_EMAIL': SU_EMAIL, 'SU_UID': SU_UID})
    def test_email_address_is_updated(self):
        User = get_user_model()
        user = User.objects.create(email=SU_EMAIL)
        EmailAddress.objects.create(
            user=user,
            email=SU_EMAIL,
            verified=False,
            primary=False
        )

        email_address = EmailAddress.objects.get(user=user, email=SU_EMAIL)
        self.assertFalse(email_address.verified)
        self.assertFalse(email_address.primary)

        call_command('pre_create_su')

        email_address = EmailAddress.objects.get(user=user, email=SU_EMAIL)
        self.assertTrue(email_address.verified)
        self.assertTrue(email_address.primary)

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_env_vars(self):
        with self.assertRaises(ImproperlyConfigured):
            call_command('pre_create_su')

    @patch.dict(os.environ, {'SU_EMAIL': SU_EMAIL, 'SU_UID': SU_UID})
    def test_idempotency(self):
        call_command('pre_create_su')
        call_command('pre_create_su')  # Run twice

        User = get_user_model()
        self.assertEqual(User.objects.filter(email=SU_EMAIL).count(), 1)
        self.assertEqual(SocialAccount.objects.filter(uid=SU_UID).count(), 1)
        self.assertEqual(EmailAddress.objects.filter(email=SU_EMAIL).count(), 1)
