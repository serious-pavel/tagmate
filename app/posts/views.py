from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404, redirect
from posts.models import Post, Tag


def post_editor(request, pk=None):
    if pk is None:
        return render(request, 'posts/post_editor.html')
    current_post = get_object_or_404(Post, pk=pk)
    context = dict()
    context['current_post'] = current_post

    if request.method == 'POST':
        tag_names_str = request.POST.get('tag_names')
        if tag_names_str:
            tag_ids = []
            for tag_name in tag_names_str.replace(",", " ").replace("#", " ").split():
                try:
                    tag, _ = Tag.objects.get_or_create(name=tag_name)
                except ValidationError as e:
                    error_message = e.message_dict.get('name', ['Invalid tag'])[0]
                    context['error_message'] = error_message
                    context['tag_names'] = tag_names_str
                    return render(request, 'posts/post_editor.html', context)
                tag_ids.append(tag.id)

            if tag_ids:
                input_tag_ids = current_post.ordered_tag_ids + tag_ids
                current_post.update_tags(input_tag_ids)

        tag_to_detach = request.POST.get('tag_to_detach')
        if tag_to_detach:
            tagset = current_post.ordered_tag_ids
            tagset.remove(int(tag_to_detach))
            current_post.update_tags(tagset)
        return render(request, 'posts/post_editor.html', context)

        # return redirect('index')  # assuming 'index' points to this page

    return render(
        request,
        template_name='posts/post_editor.html',
        context=context
    )


def create_post(request):
    new_post_title = request.POST.get('new_post_title') or 'Untitled Post'
    new_post = Post(user=request.user, title=new_post_title)
    new_post.save()
    return redirect('post_editor', pk=new_post.id)
