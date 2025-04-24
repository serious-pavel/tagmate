from django.db import models
from django.contrib.auth import get_user_model
from django.db import transaction
from django.apps import apps

User = get_user_model()


class Tag(models.Model):
    objects: models.Manager['Tag']

    name = models.CharField(max_length=64, unique=True)

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
        current_tag_ids = list(post_tags.values_list('tag_id', flat=True))

        tags_to_remove = set(current_tag_ids) - set(ordered_tag_ids)
        if tags_to_remove:
            post_tags.filter(tag_id__in=tags_to_remove).delete()

        post_tag_map = {pt.tag_id: pt for pt in PostTag.objects.filter(post=self)}
        to_update = []
        to_create = []
        for pos, tag_id in enumerate(ordered_tag_ids):
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
