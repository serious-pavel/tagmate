from django.urls import path
from posts import views as posts_views

urlpatterns = [
    path('', posts_views.post_editor, name='index'),
    path('post/<int:post_pk>', posts_views.post_editor, name='post_editor'),
    path('tg/<int:tg_pk>', posts_views.post_editor, name='tg_editor'),
    path('post/<int:post_pk>/tg/<int:tg_pk>', posts_views.post_editor,
         name='post_editor_tg'),
    path('posts/create', posts_views.create_post, name='create_post'),
    path('posts/delete/<int:post_pk>', posts_views.delete_post, name='delete_post'),
]
