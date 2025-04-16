from allauth.account.auth_backends import AuthenticationBackend as AllAuthBackend


class SocialOnlyAllAuthBackend(AllAuthBackend):
    def authenticate(self, request, **credentials):
        password = credentials.get("password")

        # Allow social login to proceed (allauth handles this internally)
        if 'sociallogin' in credentials:
            return super().authenticate(request, **credentials)

        # Explicitly disallow password-based authentication
        if password:
            return None

        return None
