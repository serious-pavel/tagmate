from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        """Populate user fields from social login data."""
        user = sociallogin.user  # Access the User instance

        # Populate custom fields
        user.full_name = sociallogin.account.extra_data.get('name', '')
        user.profile_picture = sociallogin.account.extra_data.get('picture', '')

        return user
