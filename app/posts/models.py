from django.db import models
from django.contrib.auth import get_user_model
from django.db import transaction
from django.apps import apps
from django.core.validators import RegexValidator
from django.db.models import Count
from django.db.models.signals import m2m_changed
from django.dispatch import receiver


User = get_user_model()
HASHTAG_REGEX = (
    r'^[\w'
    r'\U0001F300-\U0001F5FF'  # symbols & pictographs
    r'\U0001F600-\U0001F64F'  # emoticons
    r'\U0001F680-\U0001F6FF'  # transport & map
    r'\U0001F700-\U0001F77F'  # alchemical symbols
    r'\U0001F780-\U0001F7FF'
    r'\U0001F800-\U0001F8FF'
    r'\U0001F900-\U0001F9FF'
    r'\U0001FA00-\U0001FA6F'
    r'\U0001FA70-\U0001FAFF'
    r'\U00002702-\U000027B0'
    r'\U000024C2-\U0001F251'
    r']+$'
)

hashtag_validator = RegexValidator(
    regex=HASHTAG_REGEX,
    message="Hashtags may only contain Unicode letters, digits, underscore, or emoji."
)


class Tag(models.Model):
    objects: models.Manager['Tag']

    name = models.CharField(max_length=64, unique=True, validators=[hashtag_validator])

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        self.name = self.name.lower()  # enforce lowercase storage
        super().save(*args, **kwargs)

    def __str__(self):
        return f"#{self.name}"


class TagGroup(models.Model):
    objects: models.Manager['TagGroup']

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tag_groups')
    name = models.CharField(max_length=64)
    tags = models.ManyToManyField(Tag, related_name='tag_groups')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'name')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.name:
            counter = 1
            base_name = 'Untitled TagGroup {}'
            unique_name = base_name.format(counter)
            while TagGroup.objects.filter(name=unique_name, user=self.user).exists():
                counter += 1
                unique_name = base_name.format(counter)
            self.name = unique_name
        super().save(*args, **kwargs)

    def clear_tags(self):
        """ Deleting the Tags that are not used in any other TagGroup or ANY Post"""
        # TODO seems inefficient, fetches all Tags before Counter
        Tag.objects.annotate(
            tg_count=Count('tag_groups')
        ).annotate(
            pt_count=Count('posttag')
        ).filter(
            tag_groups=self,
            tg_count__lte=1
        ).filter(
            pt_count__lte=0
        ).delete()


class Post(models.Model):
    objects: models.Manager['Post']

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=100)
    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    tags = models.ManyToManyField(
        Tag,
        through='PostTag',
        related_name='posts'
    )

    def __str__(self):
        return self.title

    @property
    def ordered_tags(self):
        """Return ordered list of tags in Post"""
        return Tag.objects.filter(posttag__post=self).order_by('posttag__position')

    @property
    def ordered_tag_ids(self):
        """Return ordered list of tag IDs in Post"""
        return list(PostTag.objects.filter(post=self).values_list('tag_id', flat=True))

    @transaction.atomic
    def update_tags(self, ordered_tag_ids: list):
        """Rearrange, add and remove tags in Post if needed"""
        PostTag = apps.get_model('posts', 'PostTag')
        post_tags = PostTag.objects.filter(post=self)
        current_tag_ids = set(post_tags.values_list('tag_id', flat=True))

        # Deduplicate ordered_tag_ids while preserving order
        seen = set()
        unique_ordered_tag_ids = []
        for tag_id in ordered_tag_ids:
            if tag_id not in seen:
                unique_ordered_tag_ids.append(tag_id)
                seen.add(tag_id)

        # Validate ids only before attaching new tags to Post
        tag_ids_to_attach = set(unique_ordered_tag_ids) - current_tag_ids
        if tag_ids_to_attach:
            existing_tag_ids = set(Tag.objects.filter(
                id__in=ordered_tag_ids
            ).values_list('id', flat=True))

            invalid_tag_ids = [
                tag_id for tag_id in ordered_tag_ids if tag_id not in existing_tag_ids
            ]
            if invalid_tag_ids:
                raise ValueError(f"Invalid tag IDs: {invalid_tag_ids}")

        # Remove tags from Post
        tag_ids_to_detach = current_tag_ids - set(unique_ordered_tag_ids)
        if tag_ids_to_detach:
            post_tags.filter(tag_id__in=tag_ids_to_detach).delete()

        # Update tags order and create new ones (through PostTag)
        post_tag_map = {pt.tag_id: pt for pt in PostTag.objects.filter(post=self)}
        to_update = []
        to_create = []
        for pos, tag_id in enumerate(unique_ordered_tag_ids):
            pt = post_tag_map.get(tag_id)
            if pt:
                if pt.position != pos:
                    pt.position = pos
                    to_update.append(pt)
            else:
                to_create.append(PostTag(post=self, tag_id=tag_id, position=pos))
        if to_update:
            PostTag.objects.bulk_update(to_update, ['position'])
        if to_create:
            PostTag.objects.bulk_create(to_create)

        if to_update or to_create or tag_ids_to_attach or tag_ids_to_detach:
            self.save()

    @transaction.atomic
    def add_tags_from_group(self, tag_group: TagGroup):
        if tag_group.user_id != self.user_id:
            raise PermissionError("Cannot use another user's tag group.")

        tag_group_tag_ids = tag_group.tags.values_list('id', flat=True)
        current_tag_ids = self.tags.values_list('id', flat=True)
        input_tag_ids = list(current_tag_ids) + list(tag_group_tag_ids)
        self.update_tags(input_tag_ids)

    def clear_tags(self):
        """ Deleting the Tags that are not used in any other Post or ANY TagGroup"""
        # TODO seems inefficient, fetches all the PostTag before Counter
        Tag.objects.annotate(
            pt_count=Count('posttag')
        ).annotate(
            tg_count=Count('tag_groups')
        ).filter(
            posttag__post=self,
            pt_count__lte=1
        ).filter(
            tg_count__lte=0
        ).delete()


class PostTag(models.Model):
    objects: models.Manager['PostTag']

    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()

    class Meta:
        unique_together = ('post', 'tag')
        ordering = ['position']

    def __str__(self):
        return f"{self.tag} in {self.post} at {self.position}"


@receiver(m2m_changed, sender=TagGroup.tags.through)
def tag_group_tags_changed(sender, instance, action, pk_set, **kwargs):
    """
    Update TagGroup.updated_at when tags are modified.

    Handles "post_add" and "post_remove" if pk_set is not empty (actual changes),
    and always on "post_clear" (all tags removed).
    Ensures updated_at only changes on real relation updates.
    See: https://docs.djangoproject.com/en/stable/ref/signals/#m2m-changed
    """
    if (action in ("post_add", "post_remove") and pk_set) or action == "post_clear":
        instance.save()
