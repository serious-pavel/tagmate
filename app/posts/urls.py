
from django.contrib import admin
from django.urls import path, include

from allauth.account.decorators import secure_admin_login

from posts import views as posts_views


urlpatterns = [
    path('', posts_views.post_editor, name='index'),
]
