from django.shortcuts import render  # noqa
from posts.models import Post


def post_editor(request):
    latest_post = Post.objects.filter(user=request.user).order_by('-updated_at').first()
    return render(
        request,
        template_name='posts/post_editor.html',
        context={'current_post': latest_post}
    )
