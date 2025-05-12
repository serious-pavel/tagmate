import time

from django.test import TestCase
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from posts.models import Post, Tag, PostTag, TagGroup

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

    # Tests for method get_tag_id
    def test_get_tag_ids_sorts_as_post_tag_model(self):
        """Test that get_tag_id returns the correct tag id"""
        PostTag.objects.create(post=self.post, tag=self.tag1, position=1)
        PostTag.objects.create(post=self.post, tag=self.tag2, position=2)
        PostTag.objects.create(post=self.post, tag=self.tag3, position=0)

        post_tag_ids = list(
            PostTag.objects.filter(
                post=self.post
            ).order_by('position').values_list('tag_id', flat=True)
        )
        self.assertEqual(self.post.get_tag_ids(), post_tag_ids)

    def test_get_tag_ids_returns_correct_list(self):
        """Test that get_tag_ids returns a properly ordered list of tag ids"""
        pt1 = PostTag.objects.create(post=self.post, tag=self.tag1, position=0)
        pt2 = PostTag.objects.create(post=self.post, tag=self.tag2, position=1)
        pt3 = PostTag.objects.create(post=self.post, tag=self.tag3, position=2)
        self.assertEqual(
            self.post.get_tag_ids(),
            [self.tag1.id, self.tag2.id, self.tag3.id]
        )

        pt1.position = 1
        pt1.save()
        pt2.position = 0
        pt2.save()

        self.assertEqual(
            self.post.get_tag_ids(),
            [self.tag2.id, self.tag1.id, self.tag3.id]
        )

        self.post.tags.remove(self.tag2)

        # Mind the gap in tag positions if sorted manually (1, 2)
        self.assertEqual(
            self.post.get_tag_ids(),
            [self.tag1.id, self.tag3.id]
        )

        pt3.position = 0
        pt3.save()

        self.assertEqual(
            self.post.get_tag_ids(),
            [self.tag3.id, self.tag1.id]
        )

        self.post.tags.clear()
        self.assertEqual(self.post.get_tag_ids(), [])

    # Tests for method update_tags
    def test_update_tags_adds_tags_and_orders_them(self):
        """Test that update_tags correctly adds and orders tags."""
        self.post.update_tags([self.tag3.id, self.tag1.id])

        post_tags = list(PostTag.objects.filter(post=self.post))
        self.assertEqual(
            [tag.tag_id for tag in post_tags], [self.tag3.id, self.tag1.id]
        )
        self.assertEqual([tag.position for tag in post_tags], [0, 1])

    def test_update_tags_corrects_position_gap(self):
        """Test that update_tags corrects position gaps."""
        PostTag.objects.create(post=self.post, tag=self.tag1, position=0)
        PostTag.objects.create(post=self.post, tag=self.tag2, position=2)
        positions_before = list(
            PostTag.objects.filter(post=self.post).values_list('position', flat=True)
        )
        self.assertEqual(positions_before, [0, 2])

        self.post.update_tags([self.tag2.id, self.tag1.id])
        positions_after = list(
            PostTag.objects.filter(post=self.post).values_list('position', flat=True)
        )
        self.assertEqual(positions_after, [0, 1])

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

    def test_update_tags_invalid_tag_id(self):
        """Test invalid tag raises an error"""
        PostTag.objects.create(post=self.post, tag=self.tag1, position=0)
        PostTag.objects.create(post=self.post, tag=self.tag2, position=1)

        tag_ids_input = [self.tag1.id, self.tag2.id, 9999]
        with self.assertRaises(ValueError):
            self.post.update_tags(tag_ids_input)

    def test_update_tags_transaction_rollback_on_error(self):
        from unittest.mock import patch

        self.post.update_tags([self.tag1.id])
        original_tag_ids = self.post.get_tag_ids()

        # Patch bulk_create to raise error on second call
        with patch('posts.models.PostTag.objects.bulk_create',
                   side_effect=Exception("DB error")):
            with self.assertRaises(Exception):
                self.post.update_tags([self.tag1.id, self.tag2.id])

        self.post.refresh_from_db()
        self.assertEqual(self.post.get_tag_ids(), original_tag_ids)


class TagModelTests(TestCase):
    """Test cases for Tag model"""
    def test_str_representation(self):
        tag = Tag.objects.create(name="tag1")
        expected = f"#{tag.name}"
        self.assertEqual(str(tag), expected)

    def test_ordering_by_name(self):
        Tag.objects.create(name="tag1")
        Tag.objects.create(name="tag3")
        Tag.objects.create(name="tag2")
        tags = list(Tag.objects.all().values_list('name', flat=True))
        self.assertEqual(tags, ["tag1", "tag2", "tag3"])

    def test_tag_name_validation(self):
        """Test that tag names are validated"""
        from django.core.exceptions import ValidationError

        tag1 = Tag.objects.create(name="tag1")
        self.assertEqual(tag1.name, "tag1")
        tag1.full_clean()

        tag2 = Tag.objects.create(name="tag2- ")
        with self.assertRaises(ValidationError):
            tag2.full_clean()

        tag3 = Tag.objects.create(name="")
        with self.assertRaises(ValidationError):
            tag3.full_clean()

        tag4 = Tag.objects.create(name="t.ag")
        with self.assertRaises(ValidationError):
            tag4.full_clean()

        tag5 = Tag.objects.create(name="😁")
        self.assertEqual(tag5.name, "😁")
        tag5.full_clean()

    def test_tag_uniqueness_case_insensitive(self):
        """Test that tag names are case insensitive"""
        Tag.objects.create(name="Example")
        with self.assertRaises(IntegrityError):
            Tag.objects.create(name="example")

    def test_tag_name_max_length(self):
        """Test that tag names are limited to 64 characters"""
        from django.core.exceptions import ValidationError
        long_name = "a" * 65
        tag = Tag(name=long_name)
        with self.assertRaises(ValidationError):
            tag.full_clean()


class TagGroupModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='user@example.com', password='pw')
        self.post = Post.objects.create(user=self.user, title="Test Post")
        self.tag1 = Tag.objects.create(name="tag1")
        self.tag2 = Tag.objects.create(name="tag2")
        self.tag3 = Tag.objects.create(name="tag3")
        self.tag_group1 = TagGroup.objects.create(user=self.user, name="Tag Group")

    def test_str_representation(self):
        self.assertEqual(str(self.tag_group1), "Tag Group")

    def test_ordering_tags_by_name(self):
        self.tag_group1.tags.add(self.tag3)
        self.tag_group1.tags.add(self.tag2)

        grouped_tags = list(self.tag_group1.tags.all().values_list('name', flat=True))

        self.assertEqual(grouped_tags, ["tag2", "tag3"])

    def test_idempotent_add_tag_to_group(self):
        """Test that adding a tag to a group twice does not change anything"""
        self.tag_group1.tags.add(self.tag3)
        self.assertEqual(self.tag_group1.tags.count(), 1)
        self.tag_group1.tags.add(self.tag3)
        self.assertEqual(self.tag_group1.tags.count(), 1)

    def test_add_group_to_empty_post(self):
        """Test that adding a tag group to an empty post works"""
        self.assertEqual(self.post.tags.count(), 0)
        self.tag_group1.tags.add(self.tag1)

        self.post.add_tags_from_group(self.tag_group1)
        self.assertEqual(self.post.tags.count(), 1)
        self.assertEqual(self.post.tags.first(), self.tag1)

    def test_add_group_to_post_with_tags(self):
        """Test that adding a tag group to a post with tags works"""
        PostTag.objects.create(post=self.post, tag=self.tag1, position=0)
        PostTag.objects.create(post=self.post, tag=self.tag2, position=1)
        self.assertEqual(self.post.tags.count(), 2)

        self.tag_group1.tags.add(self.tag3)

        self.post.add_tags_from_group(self.tag_group1)

        self.assertEqual(self.post.tags.count(), 3)
        self.assertEqual(self.post.tags.first(), self.tag1)
        self.assertEqual(self.post.tags.last(), self.tag3)

    def test_idempotent_add_group_to_post(self):
        """Test that adding a tag group to a post twice does not change anything"""
        PostTag.objects.create(post=self.post, tag=self.tag1, position=0)
        PostTag.objects.create(post=self.post, tag=self.tag2, position=1)
        self.assertEqual(self.post.tags.count(), 2)

        self.tag_group1.tags.add(self.tag3)
        self.post.add_tags_from_group(self.tag_group1)

        self.assertEqual(self.post.tags.count(), 3)
        self.assertEqual(self.post.tags.first(), self.tag1)
        self.assertEqual(self.post.tags.last(), self.tag3)

        self.post.add_tags_from_group(self.tag_group1)

        self.assertEqual(self.post.tags.count(), 3)
        self.assertEqual(self.post.tags.first(), self.tag1)
        self.assertEqual(self.post.tags.last(), self.tag3)

    def test_add_empty_tag_group_to_post(self):
        """Test that adding an empty tag group to a post does not change anything"""
        PostTag.objects.create(post=self.post, tag=self.tag1, position=0)
        PostTag.objects.create(post=self.post, tag=self.tag2, position=1)
        self.assertEqual(self.post.tags.count(), 2)

        self.tag_group1.tags.clear()

        self.assertEqual(self.tag_group1.tags.count(), 0)

        self.post.add_tags_from_group(self.tag_group1)

        self.assertEqual(self.post.tags.count(), 2)
        self.assertEqual(self.post.tags.first(), self.tag1)
        self.assertEqual(self.post.tags.last(), self.tag2)

    def test_remove_tag_not_in_group_from_group(self):
        """Test that removing a tag not in the group does not change anything"""
        self.assertEqual(self.tag_group1.tags.count(), 0)
        self.tag_group1.tags.remove(self.tag1)
        self.assertEqual(self.tag_group1.tags.count(), 0)

    def test_delete_tag_group_does_not_delete_tags(self):
        self.assertTrue(TagGroup.objects.filter(name="Tag Group").exists())

        self.tag_group1.tags.add(self.tag1)
        self.tag_group1.tags.add(self.tag2)

        self.assertEqual(self.tag_group1.tags.count(), 2)

        tag_ids = list(self.tag_group1.tags.values_list('id', flat=True))
        self.tag_group1.delete()

        self.assertFalse(TagGroup.objects.filter(name="Tag Group").exists())
        self.assertEqual(Tag.objects.filter(id__in=tag_ids).count(), 2)
        self.assertTrue(Tag.objects.filter(name="tag1").exists())
        self.assertTrue(Tag.objects.filter(name="tag2").exists())

    def test_adding_another_users_tag_group_to_post(self):
        """Test that adding a tag group from another user does not change anything"""
        self.assertEqual(self.post.tags.count(), 0)

        another_user = User.objects.create_user(
            email='another@example.com',
            password='pw'
        )

        tag_group2 = TagGroup.objects.create(user=another_user, name="Tag Group 2")
        tag_group2.tags.add(self.tag3)

        self.assertEqual(tag_group2.tags.count(), 1)

        with self.assertRaises(PermissionError):
            self.post.add_tags_from_group(tag_group2)
        self.assertEqual(self.post.tags.count(), 0)

    def test_tag_group_name_uniqueness(self):
        """Test that tag group names are unique per user"""
        with self.assertRaises(IntegrityError):
            TagGroup.objects.create(user=self.user, name="Tag Group")

    def test_tag_group_name_can_repeat_for_different_users(self):
        """Test that two different users can use the same tag group name"""
        self.assertTrue(
            TagGroup.objects.filter(user=self.user, name="Tag Group").exists()
        )

        another_user = User.objects.create_user(
            email="another@example.com", password="pw"
        )

        TagGroup.objects.create(user=another_user, name="Tag Group")

        self.assertEqual(TagGroup.objects.filter(name="Tag Group").count(), 2)
        self.assertEqual(TagGroup.objects.filter(user=self.user).count(), 1)
        self.assertEqual(TagGroup.objects.filter(user=another_user).count(), 1)

    def test_supply_tags_at_creation_time(self):
        """Test that tags can be supplied at creation time"""
        # Technically, we can't provide tags at creation time,
        #   so we test bulk tag addition instead
        self.assertEqual(self.tag_group1.tags.count(), 0)

        self.tag_group1.tags.set([self.tag1, self.tag2])

        self.assertEqual(self.tag_group1.tags.count(), 2)


class TagGroupSignalTests(TestCase):
    """Tests for field updated_at and M2M signal"""
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='pw')
        self.tag_group1 = TagGroup.objects.create(user=self.user, name="Tag Group")
        self.tag1 = Tag.objects.create(name="tag1")
        self.tag2 = Tag.objects.create(name="tag2")
        self.time_delta = 0.1
        self.longer_time_delta = 2 * self.time_delta

    def test_updated_at_on_creation(self):
        self.assertIsNotNone(self.tag_group1.updated_at)

    def test_updated_at_on_update(self):
        old_updated_at = self.tag_group1.updated_at
        time.sleep(self.longer_time_delta)
        self.tag_group1.name = "New Name"
        self.tag_group1.save()
        self.assertNotAlmostEqual(
            self.tag_group1.updated_at.timestamp(),
            old_updated_at.timestamp(),
            delta=self.time_delta
        )

    def test_updated_at_on_add_tags(self):
        old_updated_at = self.tag_group1.updated_at
        time.sleep(self.longer_time_delta)
        self.tag_group1.tags.add(self.tag1)
        self.assertNotAlmostEqual(
            self.tag_group1.updated_at.timestamp(),
            old_updated_at.timestamp(),
            delta=self.time_delta
        )

    def test_updated_at_on_remove_tags(self):
        self.tag_group1.tags.add(self.tag1)
        old_updated_at = self.tag_group1.updated_at
        time.sleep(self.longer_time_delta)
        self.tag_group1.tags.remove(self.tag1)
        self.assertNotAlmostEqual(
            self.tag_group1.updated_at.timestamp(),
            old_updated_at.timestamp(),
            delta=self.time_delta
        )

    def test_updated_at_on_repeated_operation(self):
        """Test that updated_at is not updated when operation didn't cause changes"""
        self.tag_group1.tags.add(self.tag1)
        old_updated_at = self.tag_group1.updated_at
        time.sleep(self.longer_time_delta)
        self.tag_group1.tags.add(self.tag1)
        self.assertAlmostEqual(
            self.tag_group1.updated_at.timestamp(),
            old_updated_at.timestamp(),
            delta=self.time_delta
        )

    def test_updated_at_on_bulk_add(self):
        old_updated_at = self.tag_group1.updated_at
        time.sleep(self.longer_time_delta)
        self.tag_group1.tags.set([self.tag1, self.tag2])
        self.assertNotAlmostEqual(
            self.tag_group1.updated_at.timestamp(),
            old_updated_at.timestamp(),
            delta=self.time_delta
        )


class PostModelTests(TestCase):
    """Tests for Post model"""
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='pw')
        self.post = Post.objects.create(user=self.user, title="Test Post")
        self.time_delta = 0.1
        self.longer_time_delta = 2 * self.time_delta

    def test_str_representation(self):
        self.assertEqual(str(self.post), "Test Post")

    def test_created_at_and_updated_at_on_creation(self):
        self.assertIsNotNone(self.post.created_at)
        self.assertIsNotNone(self.post.updated_at)
        # Should be very close
        self.assertAlmostEqual(
            self.post.created_at.timestamp(),
            self.post.updated_at.timestamp(),
            delta=self.time_delta
        )

    def test_created_at_and_updated_at_on_update(self):
        old_updated_at = self.post.updated_at
        old_created_at = self.post.created_at
        time.sleep(self.longer_time_delta)
        self.post.title = "New Title"
        self.post.save()

        self.assertNotAlmostEqual(
            self.post.created_at.timestamp(),
            self.post.updated_at.timestamp(),
            delta=self.time_delta
        )

        self.assertEqual(self.post.created_at, old_created_at)
        self.assertNotEqual(self.post.updated_at, old_updated_at)

    def test_updating_tags_updates_updated_at(self):
        old_updated_at = self.post.updated_at
        time.sleep(self.longer_time_delta)
        tag = Tag.objects.create(name="tag1")
        self.post.update_tags([tag.id])

        self.assertNotAlmostEqual(
            self.post.updated_at.timestamp(),
            old_updated_at.timestamp(),
            delta=self.time_delta
        )

    def test_updating_tag_without_changes_does_not_update_updated_at(self):
        tag = Tag.objects.create(name="tag1")
        self.post.update_tags([tag.id])

        old_updated_at = self.post.updated_at
        time.sleep(self.longer_time_delta)

        self.post.update_tags([tag.id])
        self.assertAlmostEqual(
            self.post.updated_at.timestamp(),
            old_updated_at.timestamp(),
            delta=self.time_delta
        )
