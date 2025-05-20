from django.shortcuts import render, redirect
from posts.models import Post, Tag


def post_editor(request):
    latest_post = Post.objects.filter(user=request.user).order_by('-updated_at').first()

    if request.method == 'POST' and latest_post:
        tag_names_str = request.POST.get('tag_names')
        if tag_names_str:
            tag_ids = []
            for tag_name in tag_names_str.replace(",", " ").replace("#", " ").split():
                tag, created = Tag.objects.get_or_create(name=tag_name)
                if created:
                    tag.full_clean()
                    tag.save()
                tag_ids.append(tag.id)
            if tag_ids:
                input_tag_ids = latest_post.get_tag_ids() + tag_ids
                latest_post.update_tags(input_tag_ids)
        return redirect('index')  # assuming 'index' points to this page

    return render(
        request,
        template_name='posts/post_editor.html',
        context={'current_post': latest_post}
    )
