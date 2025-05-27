from django.urls import path
from posts import views as posts_views

urlpatterns = [
    path('', posts_views.post_editor, name='index'),
    path('post/<int:pk>', posts_views.post_editor, name='post_editor'),
    path('posts/create', posts_views.create_post, name='create_post'),
    path('posts/delete/<int:pk>', posts_views.delete_post, name='delete_post'),
]
