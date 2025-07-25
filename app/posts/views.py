from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import json

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
            messages.success(request, f'New Post {new_post.title} created')
            return redirect_post_editor(request, new_post.id, tg_pk)

        if action == 'create_tg':
            new_tg_name = request.POST.get('new_tg_name')
            new_tg = TagGroup(user=request.user, name=new_tg_name)
            new_tg.save()
            messages.success(request, f'New TagGroup {new_tg.name} created')
            return redirect_post_editor(request, post_pk, new_tg.id)

        tags_to_attach = request.POST.get('tags_to_attach')
        if tags_to_attach:
            if action == 'post_attach_tags':
                request.session['submitted_input_id'] = 'post-tags-to-attach'
            elif action == 'tg_attach_tags':
                request.session['submitted_input_id'] = 'tg-tags-to-attach'
            tag_ids = []
            tag_names_lst = tags_to_attach.replace(",", " ").replace("#", " ").split()
            with transaction.atomic():
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
                            # Save the value so the GET page can prefill it
                            if action == 'post_attach_tags':
                                request.session['post_tags_to_attach'] = tags_to_attach
                            elif action == 'tg_attach_tags':
                                request.session['tg_tags_to_attach'] = tags_to_attach
                            # Mark for rollback
                            transaction.set_rollback(True)
                            # Redirect prevents re-POST on reload
                            return redirect(request.path)
                    tag_ids.append(tag.id)

                if tag_ids:
                    if action == 'post_attach_tags' and current_post is not None:
                        input_tag_ids = current_post.ordered_tag_ids + tag_ids
                        current_post.update_tags(input_tag_ids)
                        return redirect(request.path)
                    if action == 'tg_attach_tags' and current_tg is not None:
                        current_tg.tags.add(*tag_ids)
                        return redirect(request.path)

        tag_to_detach = request.POST.get('tag_to_detach')
        if tag_to_detach:
            if action == 'post_detach_tag' and current_post is not None:
                tagset = current_post.ordered_tag_ids
                tagset.remove(int(tag_to_detach))
                current_post.update_tags(tagset)
                return redirect(request.path)
            if action == 'tg_detach_tag' and current_tg is not None:
                current_tg.tags.remove(int(tag_to_detach))
                return redirect(request.path)

        if action == 'copy_tags_to_tg' and current_post and current_tg:
            current_tg.tags.add(*current_post.ordered_tag_ids)

        if action == 'copy_tags_to_post' and current_tg and current_post:
            tg_tags = Tag.objects.filter(tag_groups=current_tg)
            tg_tag_ids = list(tg_tags.values_list('id', flat=True))
            current_post.update_tags(current_post.ordered_tag_ids + tg_tag_ids)

        if current_post:
            if action == 'update_post_title':
                post_title = request.POST.get('post_title')
                if post_title:
                    current_post.title = post_title
                    current_post.save()
                    messages.success(request, f'Post {current_post.title} updated')
                    return redirect(request.path)

            if action == 'update_post_desc':
                post_desc = request.POST.get('post_desc')
                if post_desc is not None:
                    current_post.description = post_desc
                    current_post.save()
                    messages.success(request, f'Post {current_post.title} updated')
                    return redirect(request.path)

            if action == 'delete_post':
                # Deleting the Tags that are not used in any other Post or ANY TagGroup
                current_post.clear_tags()

                current_post.delete()
                messages.success(request, f'Post {current_post.title} deleted')
                return redirect_post_editor(request, None, tg_pk)

        if current_tg:
            if action == 'update_tg':
                tg_name = request.POST.get('tg_name')
                current_tg.name = tg_name

                current_tg.save()
                messages.success(request, f'TagGroup {current_tg.name} updated')
                return redirect(request.path)

            if action == 'delete_tg':
                # Deleting the Tags that are not used in any other TagGroup or ANY Post
                current_tg.clear_tags()

                current_tg.delete()
                messages.success(request, f'TagGroup {current_tg.name} deleted')
                return redirect_post_editor(request, post_pk, None)

    # GET (or after redirect)
    context.update({
            'post_tags_to_attach': request.session.pop('post_tags_to_attach', ''),
            'tg_tags_to_attach': request.session.pop('tg_tags_to_attach', ''),
            'submitted_input_id': request.session.pop('submitted_input_id', ''),
        })

    return render(
        request,
        template_name='posts/post_editor.html',
        context=context
    )


@require_POST
def reorder_tags(request, post_pk):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Not authenticated"})

    data = json.loads(request.body)
    tag_order = [int(tid) for tid in data.get("tag_order", [])]

    try:
        post = Post.objects.get(id=post_pk, user=request.user)
    except Post.DoesNotExist:
        return JsonResponse({"success": False, "error": "Post not found"})

    try:
        post.update_tags(tag_order)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

    # Get the current list of tag names as a single string (e.g., "#tag1 #tag2 ...")
    tag_text = " ".join(f"#{tag.name}" for tag in post.ordered_tags)

    return JsonResponse({
        "success": True,
        "tag_text": tag_text
    })
