from django.shortcuts import render
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.google import views as google_views
from allauth.account.views import LogoutView as AllauthLogoutView
from django.http import Http404
from django.views import View


def profile(request):
    user = request.user
    context = {}
    if user.is_authenticated:
        social_acc = SocialAccount.objects.filter(
            provider='google',
            user_id=user.id,
        ).first()
        if social_acc:
            context.update({'social_acc': social_acc})

    return render(request, template_name='core/profile.html', context=context)


class GoogleLoginPostOnly(View):
    def post(self, request, *args, **kwargs):
        return google_views.oauth2_login(request)

    def get(self, request, *args, **kwargs):
        raise Http404("Page not found")


class LogoutPostOnlyView(AllauthLogoutView):
    def get(self, request, *args, **kwargs):
        raise Http404("Page not found")


class GoogleCallbackView(View):
    def get(self, request, *args, **kwargs):
        # Allow the request if it has OAuth parameters (from Google)
        if 'code' in request.GET or 'error' in request.GET:
            return google_views.oauth2_callback(request)
        else:
            # Block direct access without OAuth parameters
            raise Http404("Page not found")
