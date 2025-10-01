from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import json

from posts.models import Post, Tag, TagGroup


def field_validation_sender(request, val_error: ValidationError):
    """Sends a message for any field that failed validation"""
    for field, messages_list in val_error.message_dict.items():
        for msg in messages_list:
            messages.error(request, f"{field.capitalize()}: {msg}")


def redirect_post_editor(request, post_pk=None, tg_pk=None):
    if tg_pk is not None and post_pk is not None:
        return redirect('post_tg_editor', post_pk=post_pk, tg_pk=tg_pk)
    if tg_pk is not None:
        return redirect('tg_editor', tg_pk=tg_pk)
    if post_pk is not None:
        return redirect('post_editor', post_pk=post_pk)
    return redirect('index')


@login_required(login_url='profile')
def post_editor(request, post_pk=None, tg_pk=None):
    messages.info(request, '')
    context = dict()
    current_post, current_tg = None, None

    if post_pk is not None:
        current_post = get_object_or_404(Post, pk=post_pk, user=request.user)
        request.session['opened_post_id'] = current_post.id
    else:
        opened_post_id = request.session.get('opened_post_id')
        if opened_post_id and str(opened_post_id).isdigit():
            opened_post = Post.objects.filter(
                user=request.user,
                pk=int(opened_post_id)
            ).first()
            if opened_post:
                current_post = opened_post

    context['current_post'] = current_post

    if tg_pk is not None:
        current_tg = get_object_or_404(TagGroup, pk=tg_pk, user=request.user)
        request.session['opened_tg_id'] = current_tg.id
    else:
        opened_tg_id = request.session.get('opened_tg_id')
        if opened_tg_id and str(opened_tg_id).isdigit():
            opened_tg = TagGroup.objects.filter(
                user=request.user,
                pk=int(opened_tg_id)
            ).first()
            if opened_tg:
                current_tg = opened_tg

    context['current_tg'] = current_tg

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_post':
            new_post_title = request.POST.get('new_item_name') or 'Untitled Post'
            new_post = Post(user=request.user, title=new_post_title)
            try:
                new_post.full_clean()
            except ValidationError as e:
                field_validation_sender(request, e)
                return redirect(request.path)
            new_post.save()
            messages.success(request, f'New Post {new_post.title} created')
            return redirect_post_editor(request, new_post.id, tg_pk)

        if action == 'create_tg':
            new_tg_name = request.POST.get('new_item_name')
            new_tg = TagGroup(user=request.user, name=new_tg_name)
            try:
                new_tg.full_clean()
            except ValidationError as e:
                field_validation_sender(request, e)
                return redirect(request.path)
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
                        input_tag_ids = current_tg.ordered_tag_ids + tag_ids
                        current_tg.update_tags(input_tag_ids)
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
            current_tg.update_tags(
                current_tg.ordered_tag_ids + current_post.ordered_tag_ids
            )

        if action == 'copy_tags_to_post' and current_tg and current_post:
            current_post.update_tags(
                current_post.ordered_tag_ids + current_tg.ordered_tag_ids
            )

        if current_post:
            if action == 'update_post_title':
                post_title = request.POST.get('post_title')
                if post_title:
                    current_post.title = post_title
                    try:
                        current_post.full_clean()
                    except ValidationError as e:
                        field_validation_sender(request, e)
                        return redirect(request.path)
                    current_post.save()
                    messages.success(request, f'Post {current_post.title} updated')
                    return redirect(request.path)

            if action == 'update_post_desc':
                post_desc = request.POST.get('post_desc')
                if post_desc is not None:
                    current_post.description = post_desc
                    try:
                        current_post.full_clean()
                    except ValidationError as e:
                        field_validation_sender(request, e)
                        return redirect(request.path)
                    current_post.save()
                    messages.success(request, f'Post {current_post.title} updated')
                    return redirect(request.path)

            if action == 'delete_post':
                current_post.delete()
                request.session.pop('opened_post_id')
                messages.success(request, f'Post {current_post.title} deleted')
                return redirect_post_editor(request, None, tg_pk)

            if action == 'close_current_post':
                request.session.pop('opened_post_id')
                return redirect_post_editor(request, None, tg_pk)

        if current_tg:
            if action == 'update_tg':
                tg_name = request.POST.get('tg_name')
                current_tg.name = tg_name
                try:
                    current_tg.full_clean()
                except ValidationError as e:
                    field_validation_sender(request, e)
                    return redirect(request.path)
                current_tg.save()
                messages.success(request, f'TagGroup {current_tg.name} updated')
                return redirect(request.path)

            if action == 'delete_tg':
                current_tg.delete()
                request.session.pop('opened_tg_id')
                messages.success(request, f'TagGroup {current_tg.name} deleted')
                return redirect_post_editor(request, post_pk, None)

            if action == 'close_current_tg':
                request.session.pop('opened_tg_id')
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
def reorder_tags(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Not authenticated"})

    data = json.loads(request.body)
    item_type = data.get("item_type")
    if item_type == "post":
        item_model = Post
    else:
        item_model = TagGroup
    try:
        item = item_model.objects.get(id=data.get("item_id"), user=request.user)
    except item_model.DoesNotExist:
        return JsonResponse({"success": False, "error": "Item not found"})

    tag_order = [int(tid) for tid in data.get("tag_order", [])]

    try:
        item.update_tags(tag_order)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

    response_data = {"success": True}
    # Get the current list of tag names as a single string (e.g., "#tag1 #tag2 ...")
    if item_type == "post":
        tag_text = " ".join(f"#{tag.name}" for tag in item.ordered_tags)
        response_data["tag_text"] = tag_text

    return JsonResponse(response_data)
