from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from posts.models import Post, Tag


def post_editor(request, pk=None):
    if pk is None:
        messages.info(request, '')
        return render(request, 'posts/post_editor.html')
    current_post = get_object_or_404(Post, pk=pk, user=request.user)
    context = dict()
    context['current_post'] = current_post

    if request.method == 'POST':
        tag_names_str = request.POST.get('tag_names')
        if tag_names_str:
            tag_ids = []
            for tag_name in tag_names_str.replace(",", " ").replace("#", " ").split():
                tag = Tag.objects.filter(name=tag_name).first()
                if tag is None:
                    tag = Tag(name=tag_name)
                    try:
                        tag.full_clean()
                        tag.save()
                    except ValidationError as e:
                        error_message = e.message_dict.get('name', ['Invalid tag'])[0]
                        messages.error(request, error_message)
                        context['tag_names'] = tag_names_str
                        return render(request, 'posts/post_editor.html', context)
                tag_ids.append(tag.id)

            if tag_ids:
                input_tag_ids = current_post.ordered_tag_ids + tag_ids
                current_post.update_tags(input_tag_ids)
                return redirect('post_editor', pk=current_post.id)

        tag_to_detach = request.POST.get('tag_to_detach')
        if tag_to_detach:
            tagset = current_post.ordered_tag_ids
            tagset.remove(int(tag_to_detach))
            current_post.update_tags(tagset)
        return redirect('post_editor', pk=current_post.id)

        # return redirect('index')  # assuming 'index' points to this page

    return render(
        request,
        template_name='posts/post_editor.html',
        context=context
    )


def create_post(request):
    if request.method != 'POST':
        return redirect('index')
    new_post_title = request.POST.get('new_post_title') or 'Untitled Post'
    new_post = Post(user=request.user, title=new_post_title)
    new_post.save()
    messages.success(request, f'New post {new_post.title} created')
    return redirect('post_editor', pk=new_post.id)


def delete_post(request, pk):
    if request.method != 'POST':
        return redirect('index')
    action = request.POST.get('action')
    if action != 'delete_post':
        return redirect('index')

    post = get_object_or_404(Post, pk=pk)
    post.delete()
    messages.success(request, f'Post {post.title} deleted')
    return redirect('index')
