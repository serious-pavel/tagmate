from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.title
