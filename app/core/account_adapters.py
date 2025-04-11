from allauth.account.adapter import DefaultAccountAdapter


class NoSignUpAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False

    def authenticate(self, request, **credentials):
        return None
