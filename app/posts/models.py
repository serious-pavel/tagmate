from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def save(self, *args, **kwargs):
        self.name = self.name.lower()  # enforce lowercase storage
        super().save(*args, **kwargs)

    def __str__(self):
        return f"#{self.name}"


class TagGroup(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tag_groups')
    name = models.CharField(max_length=64)
    tags = models.ManyToManyField(Tag, related_name='tag_groups')

    def __str__(self):
        return self.name


class Post(models.Model):
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

    def set_tag_order(self, ordered_tag_ids):
        """
        Reorders tags for this post according to the ordered list of tag ids.
        Any missing or extra ids in the list are ignored/skipped.
        """
        post_tags = list(self.posttag_set.select_related('tag'))
        tag_map = {pt.tag_id: pt for pt in post_tags}
        updated_post_tags = []

        for position, tag_id in enumerate(ordered_tag_ids):
            post_tag = tag_map.get(tag_id)
            if post_tag:
                post_tag.position = position
                updated_post_tags.append(post_tag)

        PostTag.objects.bulk_update(updated_post_tags, ['position'])

    def update_tags(self, ordered_tag_ids):
        current_tag_ids = set(self.posttag_set.values_list('tag_id', flat=True))
        new_tag_ids = set(ordered_tag_ids)

        tags_to_delete = current_tag_ids - new_tag_ids
        self.posttag_set.filter(tag_id__in=tags_to_delete).delete()

        # Reorder tags
        self.set_tag_order(ordered_tag_ids)


class PostTag(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()

    class Meta:
        unique_together = ('post', 'tag')
        ordering = ['position']

    def __str__(self):
        return f"{self.tag} in {self.post} at {self.position}"
