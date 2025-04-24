from django.test import TestCase
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from posts.models import Post, Tag, PostTag

User = get_user_model()


class PostTagModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='u@example.com', password='pw')
        self.post = Post.objects.create(user=self.user, title="Test", description="desc")
        self.tag1 = Tag.objects.create(name="tag1")
        self.tag2 = Tag.objects.create(name="tag2")
        self.tag3 = Tag.objects.create(name="tag3")

    def test_unique_together_constraint(self):
        """Test attempt to create duplicates raises an error"""
        PostTag.objects.create(post=self.post, tag=self.tag1, position=0)
        with self.assertRaises(IntegrityError):
            # Duplicate (post, tag) should raise an IntegrityError
            PostTag.objects.create(post=self.post, tag=self.tag1, position=1)
