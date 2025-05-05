from django.db import models
from django.contrib.auth import get_user_model
from django.db import transaction
from django.apps import apps
from django.core.validators import RegexValidator


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

    def __str__(self):
        return self.name


class Post(models.Model):
    objects: models.Manager['Post']

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=100)
    description = models.TextField()

    tags = models.ManyToManyField(
        Tag,
        through='PostTag',
        related_name='posts'
    )

    def __str__(self):
        return self.title

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

    @transaction.atomic
    def add_tags_from_group(self, tag_group: TagGroup):
        tag_group_tag_ids = tag_group.tags.values_list('id', flat=True)
        current_tag_ids = self.tags.values_list('id', flat=True)
        input_tag_ids = list(current_tag_ids) + list(tag_group_tag_ids)
        self.update_tags(input_tag_ids)


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
