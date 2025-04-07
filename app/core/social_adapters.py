from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        """Populate user fields from social login data."""
        user = sociallogin.user  # Access the User instance

        # Populate custom fields
        user.full_name = sociallogin.account.extra_data.get('name', '')
        user.profile_picture = sociallogin.account.extra_data.get(
            'picture', ''
        )

        return user

    def pre_social_login(self, request, sociallogin):
        """
        Refresh data if changed. Called with every social login.
        """
        if sociallogin.is_existing:
            user = sociallogin.user
            extra_data = sociallogin.account.extra_data

            # Update the fields if they’ve changed
            full_name = extra_data.get('name', '')
            profile_pic = extra_data.get('picture', '')

            if full_name and user.full_name != full_name:
                user.full_name = full_name

            if profile_pic and user.profile_picture != profile_pic:
                user.profile_picture = profile_pic

            user.save()

        super().pre_social_login(request, sociallogin)
