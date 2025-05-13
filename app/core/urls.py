from django.urls import path

from allauth.socialaccount.providers.google import views as google_views
from allauth.account.views import LogoutView
from allauth.socialaccount.views import (
    ConnectionsView,
    LoginCancelledView,
    LoginErrorView,
    # SignupView
)
from . import views as core_views


urlpatterns = [
    path('google/login/', google_views.oauth2_login, name='google_login'),
    path('google/login/callback/', google_views.oauth2_callback, name='google_callback'),
    path('logout/', LogoutView.as_view(), name='account_logout'),
    path('social/connections/', ConnectionsView.as_view(), name='social_connections'),
    # path('social/signup/', SignupView.as_view(), name='social_signup'),
    path('social/login/cancelled/', LoginCancelledView.as_view(),
         name='social_login_cancelled'),
    path('social/login/error/', LoginErrorView.as_view(), name='social_login_error'),
    path('profile/', core_views.profile, name='profile'),
]
