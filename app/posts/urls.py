from django.urls import path
from posts import views as posts_views

urlpatterns = [
    path('', posts_views.post_editor, name='index'),
]
