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
from django.views.generic import TemplateView

import core.views as core_views

from allauth.account.decorators import secure_admin_login

admin.autodiscover()
admin.site.login = secure_admin_login(admin.site.login)

handler400 = "core.views.bad_request"
handler403 = "core.views.permission_denied"
handler404 = "core.views.page_not_found"
handler500 = "core.views.server_error"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('core.urls')),
    path('', include('posts.urls')),
    path('health-check/', core_views.health_check, name='health_check'),
    path("robots.txt", TemplateView.as_view(
        template_name="robots.txt", content_type="text/plain")
         )
]
