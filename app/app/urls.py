"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from allauth.socialaccount.providers.google import views as google_views
from allauth.account.views import LogoutView
from allauth.socialaccount.views import (
    ConnectionsView,
    LoginCancelledView,
    LoginErrorView,
    # SignupView
)
from allauth.account.decorators import secure_admin_login

from core import views as core_views

account_urlpatterns = [
    path('google/login/', google_views.oauth2_login, name='google_login'),
    path('google/login/callback/', google_views.oauth2_callback, name='google_callback'),
    path('logout/', LogoutView.as_view(), name='account_logout'),
    path('social/connections/', ConnectionsView.as_view(), name='social_connections'),
    # path('social/signup/', SignupView.as_view(), name='social_signup'),
    path('social/login/cancelled/', LoginCancelledView.as_view(),
         name='social_login_cancelled'),
    path('social/login/error/', LoginErrorView.as_view(), name='social_login_error'),
]

admin.autodiscover()
admin.site.login = secure_admin_login(admin.site.login)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include(account_urlpatterns)),
    path('', core_views.index, name='index'),
]
