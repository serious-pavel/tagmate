from django.core.exceptions import ValidationError
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from posts.models import Post, Tag, TagGroup


def redirect_post_editor(request, post_pk=None, tg_pk=None):
    if tg_pk is not None and post_pk is not None:
        return redirect('post_tg_editor', post_pk=post_pk, tg_pk=tg_pk)
    if tg_pk is not None:
        return redirect('tg_editor', tg_pk=tg_pk)
    if post_pk is not None:
        return redirect('post_editor', post_pk=post_pk)
    return redirect('index')


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
        action = request.POST.get('action')

        if action == 'create_post':
            new_post_title = request.POST.get('new_post_title') or 'Untitled Post'
            new_post = Post(user=request.user, title=new_post_title)
            new_post.save()
            messages.success(request, f'New post {new_post.title} created')
            return redirect_post_editor(request, new_post.id, tg_pk)

        if action == 'create_tg':
            new_tg_name = request.POST.get('new_tg_name') or 'Untitled TagGroup'
            new_tg = TagGroup(user=request.user, name=new_tg_name)
            new_tg.save()
            messages.success(request, f'New post {new_tg.name} created')
            return redirect_post_editor(request, post_pk, new_tg.id)

        if current_post:
            tag_names_str = request.POST.get('tag_names')
            if tag_names_str:
                tag_ids = []
                tag_names_lst = tag_names_str.replace(",", " ").replace("#", " ").split()
                for tag_name in tag_names_lst:
                    tag = Tag.objects.filter(name=tag_name).first()
                    if tag is None:
                        tag = Tag(name=tag_name)
                        try:
                            tag.full_clean()
                            tag.save()
                        except ValidationError as e:
                            error_msg = e.message_dict.get('name', ['Invalid tag'])[0]
                            messages.error(request, error_msg)
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

            if action == 'update_post':
                post_title = request.POST.get('post_title')
                post_desc = request.POST.get('post_desc')

                current_post.title = post_title
                current_post.description = post_desc
                current_post.save()

                messages.success(request, f'Post {current_post.title} updated')
                return redirect_post_editor(request, current_post.id, tg_pk)

            if action == 'delete_post':
                # Fetching and deleting the Tags that are not used in any other post
                # TODO seems inefficient, fetches all the PostTag before Counter
                # TODO add counter for TagGroups (should be 0)
                counted_tags = Tag.objects.annotate(pt_count=Count('posttag'))
                counted_tags.filter(posttag__post=current_post, pt_count__lte=1).delete()

                current_post.delete()
                messages.success(request, f'Post {current_post.title} deleted')
                return redirect_post_editor(request, None, tg_pk)

            return redirect_post_editor(request, current_post.id, tg_pk)

    return render(
        request,
        template_name='posts/post_editor.html',
        context=context
    )
