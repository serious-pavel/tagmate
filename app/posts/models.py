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


class PostTag(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()

    class Meta:
        unique_together = ('post', 'tag')
        ordering = ['position']

    def __str__(self):
        return f"{self.tag} in {self.post} at {self.position}"
