from django.urls import path
from posts import views as posts_views

urlpatterns = [
    path('', posts_views.post_editor, name='index'),
    path('post/<int:post_pk>', posts_views.post_editor, name='post_editor'),
    path('tg/<int:tg_pk>', posts_views.post_editor, name='tg_editor'),
    path('post/<int:post_pk>/tg/<int:tg_pk>', posts_views.post_editor,
         name='post_tg_editor'),
]
