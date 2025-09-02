from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import logout
from allauth.socialaccount.providers.google import views as google_views
from allauth.account.views import LogoutView as AllauthLogoutView
from django.http import Http404, JsonResponse
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


@login_required
@require_http_methods(["POST"])
def delete_account(request):
    """Delete the current user's account and all associated data"""
    user = request.user

    logout(request)

    user.delete()

    messages.success(request, "Your account has been successfully deleted.")
    return redirect('profile')


def health_check(request):
    return JsonResponse({"status": "ok"})
