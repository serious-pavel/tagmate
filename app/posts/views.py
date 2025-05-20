from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from posts.models import Post, Tag


def post_editor(request):
    context = dict()
    latest_post = Post.objects.filter(user=request.user).order_by('-updated_at').first()
    context['current_post'] = latest_post

    if request.method == 'POST' and latest_post:
        tag_names_str = request.POST.get('tag_names')
        if tag_names_str:
            tag_ids = []
            for tag_name in tag_names_str.replace(",", " ").replace("#", " ").split():

                # Tag validation BEFORE creation
                tag = Tag(name=tag_name)
                try:
                    tag.full_clean()
                except ValidationError as e:
                    error_message = e.message_dict.get('name', ['Invalid tag'])[0]
                    context['error_message'] = error_message
                    context['tag_names'] = tag_names_str
                    return render(request, 'posts/post_editor.html', context)

                tag, created = Tag.objects.get_or_create(name=tag_name)
                tag_ids.append(tag.id)
            if tag_ids:
                input_tag_ids = latest_post.get_tag_ids() + tag_ids
                latest_post.update_tags(input_tag_ids)
        return redirect('index')  # assuming 'index' points to this page

    return render(
        request,
        template_name='posts/post_editor.html',
        context=context
    )
