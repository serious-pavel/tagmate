from django.core.exceptions import ValidationError
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from posts.models import Post, Tag, TagGroup


def redirect_post_editor(request, post_pk, tg_pk):
    if tg_pk is not None:
        return redirect('post_editor_tg', post_pk=post_pk, tg_pk=tg_pk)
    return redirect('post_editor', post_pk=post_pk)


def post_editor(request, post_pk=None, tg_pk=None):
    messages.info(request, '')
    context = dict()
    current_post, current_tg = None, None

    if post_pk is not None:
        current_post = get_object_or_404(Post, pk=post_pk, user=request.user)
        context['current_post'] = current_post

    if tg_pk is not None:
        current_tg = TagGroup.objects.filter(pk=tg_pk).first()
        context['current_tg'] = current_tg

    if request.method == 'POST':
        if current_post:
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
                    return redirect_post_editor(request, current_post.id, tg_pk)

            tag_to_detach = request.POST.get('tag_to_detach')
            if tag_to_detach:
                tagset = current_post.ordered_tag_ids
                tagset.remove(int(tag_to_detach))
                current_post.update_tags(tagset)
            return redirect_post_editor(request, current_post.id, tg_pk)

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
    return redirect('post_editor', post_pk=new_post.id)


def delete_post(request, post_pk):
    if request.method != 'POST':
        return redirect('index')
    action = request.POST.get('action')
    if action != 'delete_post':
        return redirect('index')

    post = get_object_or_404(Post, pk=post_pk)

    # Fetching and deleting the Tags that are not used in any other post
    # TODO seems inefficient, fetches all the PostTag before Counter
    # TODO add counter for TagGroups (should be 0)
    counted_tags = Tag.objects.annotate(pt_count=Count('posttag'))
    counted_tags.filter(posttag__post=post, pt_count__lte=1).delete()

    post.delete()
    messages.success(request, f'Post {post.title} deleted')
    return redirect('index')


def update_post(request, post_pk):
    if request.method != 'POST':
        return redirect('index')
    post_title = request.POST.get('post_title')
    post_desc = request.POST.get('post_desc')

    post = get_object_or_404(Post, pk=post_pk)
    post.title = post_title
    post.description = post_desc
    post.save()

    messages.success(request, f'Post {post.title} updated')
    return redirect('post_editor', post_pk=post.id)
