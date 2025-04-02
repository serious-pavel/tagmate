from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        """Populate user fields from social login data."""
        user = super().populate_user(request, sociallogin, data)

        user.name = data.get('name', '')
        # user.profile_picture = data.get('picture') or data.get('avatar_url')
        user.profile_picture = data.get('picture', '')

        return user
