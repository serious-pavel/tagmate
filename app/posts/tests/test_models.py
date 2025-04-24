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
        """Test attempt to create duplicates raises IntegrityError"""
        PostTag.objects.create(post=self.post, tag=self.tag1, position=0)
        with self.assertRaises(IntegrityError):
            PostTag.objects.create(post=self.post, tag=self.tag1, position=1)

    def test_cascade_delete_post(self):
        """Test PostTag is deleted when the Post is deleted"""
        pt = PostTag.objects.create(post=self.post, tag=self.tag1, position=0)
        self.post.delete()
        self.assertFalse(PostTag.objects.filter(pk=pt.pk).exists())

    def test_str_representation(self):
        pt = PostTag.objects.create(post=self.post, tag=self.tag2, position=2)
        expected = f"{pt.tag} in {pt.post} at {pt.position}"
        self.assertEqual(str(pt), expected)

    def test_ordering_by_position(self):
        PostTag.objects.create(post=self.post, tag=self.tag2, position=2)
        PostTag.objects.create(post=self.post, tag=self.tag1, position=0)
        PostTag.objects.create(post=self.post, tag=self.tag3, position=1)
        positions = list(
            PostTag.objects.filter(post=self.post).values_list('position', flat=True)
        )
        self.assertEqual(positions, [0, 1, 2])

    # Tests for method update_tags
    def test_update_tags_adds_tags_and_orders_them(self):
        """Test that update_tags correctly adds and orders tags."""
        self.post.update_tags([self.tag3.id, self.tag1.id])

        post_tags = list(PostTag.objects.filter(post=self.post))
        self.assertEqual(
            [tag.tag_id for tag in post_tags], [self.tag3.id, self.tag1.id]
        )
        self.assertEqual([tag.position for tag in post_tags], [0, 1])

    def test_update_tags_removes_unlisted_tags(self):
        """Test that update_tags removes tags not in the given list."""
        PostTag.objects.create(post=self.post, tag=self.tag1, position=0)
        PostTag.objects.create(post=self.post, tag=self.tag2, position=1)

        self.post.update_tags([self.tag1.id])

        post_tags = list(PostTag.objects.filter(post=self.post))
        self.assertEqual(
            [tag.tag_id for tag in post_tags], [self.tag1.id]
        )
        self.assertEqual([tag.position for tag in post_tags], [0])

    def test_update_tags_reorders_existing_tags(self):
        """Test that update_tags changes the order of existing tags."""
        PostTag.objects.create(post=self.post, tag=self.tag1, position=0)
        PostTag.objects.create(post=self.post, tag=self.tag2, position=1)

        self.post.update_tags([self.tag2.id, self.tag1.id])

        post_tags = list(PostTag.objects.filter(post=self.post))
        self.assertEqual(
            [tag.tag_id for tag in post_tags], [self.tag2.id, self.tag1.id]
        )
        self.assertEqual([tag.position for tag in post_tags], [0, 1])

    def test_update_tags_idempotent_when_order_and_tags_unchanged(self):
        """Calling update_tags with the current order does not change anything."""
        PostTag.objects.create(post=self.post, tag=self.tag1, position=0)
        PostTag.objects.create(post=self.post, tag=self.tag2, position=1)

        self.post.update_tags([self.tag1.id, self.tag2.id])

        post_tags = list(PostTag.objects.filter(post=self.post))
        self.assertEqual(
            [tag.tag_id for tag in post_tags], [self.tag1.id, self.tag2.id]
        )
        self.assertEqual([tag.position for tag in post_tags], [0, 1])

    def test_update_tags_combined_operation(self):
        """Test that add, remove and rearrange operations work together"""
        PostTag.objects.create(post=self.post, tag=self.tag1, position=0)
        PostTag.objects.create(post=self.post, tag=self.tag2, position=1)

        self.tag4 = Tag.objects.create(name="tag4")
        tag_ids_input = [self.tag3.id, self.tag1.id, self.tag4.id]

        self.post.update_tags(tag_ids_input)

        post_tags = list(PostTag.objects.filter(post=self.post))
        self.assertEqual(
            [tag.tag_id for tag in post_tags], tag_ids_input
        )
        self.assertEqual([tag.position for tag in post_tags], [0, 1, 2])

    def test_update_tags_empty_list_clears_tags_from_post(self):
        """Test that an empty list removes tags from a post"""
        PostTag.objects.create(post=self.post, tag=self.tag1, position=0)
        PostTag.objects.create(post=self.post, tag=self.tag2, position=1)

        tag_ids_input = []
        self.post.update_tags(tag_ids_input)

        post_tags = list(PostTag.objects.filter(post=self.post))

        self.assertEqual(
            [tag.tag_id for tag in post_tags], tag_ids_input
        )

    def test_update_tags_duplicate_input(self):
        """Test that duplicated tags in input don't cause inconsistencies"""
        PostTag.objects.create(post=self.post, tag=self.tag1, position=0)

        tag_ids_input = [
            self.tag1.id, self.tag2.id, self.tag2.id, self.tag3.id
        ]

        self.post.update_tags(tag_ids_input)

        post_tags = list(PostTag.objects.filter(post=self.post))

        self.assertEqual(
            [tag.tag_id for tag in post_tags],
            [self.tag1.id, self.tag2.id, self.tag3.id]
        )
        self.assertNotEqual(
            [tag.tag_id for tag in post_tags], tag_ids_input
        )
        self.assertEqual([tag.position for tag in post_tags], [0, 1, 2])
