"""
Django command for pre-creating superusers
"""
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand

from django.contrib.auth import get_user_model
from allauth.socialaccount.models import SocialAccount
from allauth.account.models import EmailAddress

import os


class Command(BaseCommand):
    """Django command to pre-create a superuser with Google auth"""

    def handle(self, *args, **options):
        uid = os.getenv('SU_UID')
        email = os.getenv('SU_EMAIL')

        if not uid or not email:
            raise ImproperlyConfigured(
                "Env vars SU_UID and SU_EMAIL must be set"
            )

        User = get_user_model()

        # Create the user
        user, _ = User.objects.get_or_create(email=email)
        update_fields = []

        if user.has_usable_password():
            user.set_unusable_password()
            update_fields.append('password')

        if not user.is_staff:
            user.is_staff = True
            update_fields.append('is_staff')

        if not user.is_superuser:
            user.is_superuser = True
            update_fields.append('is_superuser')

        if update_fields:
            user.save(update_fields=update_fields)

        # Link the social account
        social_account, _ = SocialAccount.objects.get_or_create(
            user=user,
            provider='google',
            uid=uid,
        )

        # Create EmailAddress
        email_address, created = EmailAddress.objects.get_or_create(
            user=user,
            email=email,
            defaults={
                'verified': True,
                'primary': True,
            }
        )

        if not created:
            if not email_address.verified or not email_address.primary:
                email_address.verified = True
                email_address.primary = True
                email_address.save()
