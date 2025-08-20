import time

from django.test import TestCase
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from posts.models import Post, Tag, PostTag, TagGroup, TagGroupTag

User = get_user_model()


class PostTagModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='u@example.com', password='pw')
        self.post = Post.objects.create(user=self.user, title='Test', description='desc')
        self.tag1 = Tag.objects.create(name='tag1')
        self.tag2 = Tag.objects.create(name='tag2')
        self.tag3 = Tag.objects.create(name='tag3')

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
        expected = f'{pt.tag} in {pt.post} at {pt.position}'
        self.assertEqual(str(pt), expected)

    def test_ordering_by_position(self):
        PostTag.objects.create(post=self.post, tag=self.tag2, position=2)
        PostTag.objects.create(post=self.post, tag=self.tag1, position=0)
        PostTag.objects.create(post=self.post, tag=self.tag3, position=1)
        positions = list(
            PostTag.objects.filter(post=self.post).values_list('position', flat=True)
        )
        self.assertEqual(positions, [0, 1, 2])

    # Tests for properties ordered_tag_ids and ordered_tags
    def test_ordered_tag_ids_sorts_as_post_tag_model(self):
        """Test that get_tag_id returns the correct tag id"""
        PostTag.objects.create(post=self.post, tag=self.tag1, position=1)
        PostTag.objects.create(post=self.post, tag=self.tag2, position=2)
        PostTag.objects.create(post=self.post, tag=self.tag3, position=0)

        post_tag_ids = list(
            PostTag.objects.filter(
                post=self.post
            ).order_by('position').values_list('tag_id', flat=True)
        )
        self.assertEqual(self.post.ordered_tag_ids, post_tag_ids)

    def test_ordered_tag_ids_returns_correct_list(self):
        """Test that ordered_tag_ids returns a properly ordered list of tag ids"""
        pt1 = PostTag.objects.create(post=self.post, tag=self.tag1, position=0)
        pt2 = PostTag.objects.create(post=self.post, tag=self.tag2, position=1)
        pt3 = PostTag.objects.create(post=self.post, tag=self.tag3, position=2)
        self.assertEqual(
            self.post.ordered_tag_ids,
            [self.tag1.id, self.tag2.id, self.tag3.id]
        )

        pt1.position = 1
        pt1.save()
        pt2.position = 0
        pt2.save()

        self.assertEqual(
            self.post.ordered_tag_ids,
            [self.tag2.id, self.tag1.id, self.tag3.id]
        )

        self.post.tags.remove(self.tag2)

        # Mind the gap in tag positions if sorted manually (1, 2)
        self.assertEqual(
            self.post.ordered_tag_ids,
            [self.tag1.id, self.tag3.id]
        )

        pt3.position = 0
        pt3.save()

        self.assertEqual(
            self.post.ordered_tag_ids,
            [self.tag3.id, self.tag1.id]
        )

        self.post.tags.clear()
        self.assertEqual(self.post.ordered_tag_ids, [])

    def test_ordered_tags_returns_same_tags_as_ordered_tag_ids(self):
        PostTag.objects.create(post=self.post, tag=self.tag3, position=0)
        PostTag.objects.create(post=self.post, tag=self.tag1, position=1)

        ids_by_ordered_tags = list(self.post.ordered_tags.values_list('id', flat=True))
        self.assertEqual(
            self.post.ordered_tag_ids,
            ids_by_ordered_tags
        )

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

        self.tag4 = Tag.objects.create(name='tag4')
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
        original_tag_ids = self.post.ordered_tag_ids

        # Patch bulk_create to raise error on second call
        with patch('posts.models.PostTag.objects.bulk_create',
                   side_effect=Exception('DB error')):
            with self.assertRaises(Exception):
                self.post.update_tags([self.tag1.id, self.tag2.id])

        self.post.refresh_from_db()
        self.assertEqual(self.post.ordered_tag_ids, original_tag_ids)


class TagGroupTagModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='u@example.com', password='pw')
        self.tg = TagGroup.objects.create(user=self.user, name='Test')
        self.tag1 = Tag.objects.create(name='tag1')
        self.tag2 = Tag.objects.create(name='tag2')
        self.tag3 = Tag.objects.create(name='tag3')

    def test_unique_together_constraint(self):
        """Test attempt to create duplicates raises IntegrityError"""
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag1, position=0)
        with self.assertRaises(IntegrityError):
            TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag1, position=1)

    def test_cascade_delete_post(self):
        """Test TagGroupTag is deleted when the TagGroup is deleted"""
        tgt = TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag1, position=0)
        self.tg.delete()
        self.assertFalse(TagGroupTag.objects.filter(pk=tgt.pk).exists())

    def test_str_representation(self):
        tgt = TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag2, position=2)
        expected = f'{tgt.tag} in {tgt.tag_group} at {tgt.position}'
        self.assertEqual(str(tgt), expected)

    def test_ordering_by_position(self):
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag2, position=2)
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag1, position=0)
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag3, position=1)
        positions = list(
            TagGroupTag.objects.filter(tag_group=self.tg).values_list(
                'position', flat=True
            )
        )
        self.assertEqual(positions, [0, 1, 2])

    # Tests for properties ordered_tag_ids and ordered_tags
    def test_ordered_tag_ids_sorts_as_post_tag_model(self):
        """Test that get_tag_id returns the correct Tag id"""
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag1, position=1)
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag2, position=2)
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag3, position=0)

        tg_tag_ids = list(
            TagGroupTag.objects.filter(
                tag_group=self.tg
            ).order_by('position').values_list('tag_id', flat=True)
        )
        self.assertEqual(self.tg.ordered_tag_ids, tg_tag_ids)

    def test_ordered_tag_ids_returns_correct_list(self):
        """Test that ordered_tag_ids returns a properly ordered list of Tag ids"""
        tgt1 = TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag1, position=0)
        tgt2 = TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag2, position=1)
        tgt3 = TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag3, position=2)
        self.assertEqual(
            self.tg.ordered_tag_ids,
            [self.tag1.id, self.tag2.id, self.tag3.id]
        )

        tgt1.position = 1
        tgt1.save()
        tgt2.position = 0
        tgt2.save()

        self.assertEqual(
            self.tg.ordered_tag_ids,
            [self.tag2.id, self.tag1.id, self.tag3.id]
        )

        self.tg.tags.remove(self.tag2)

        # Mind the gap in tag positions if sorted manually (1, 2)
        self.assertEqual(
            self.tg.ordered_tag_ids,
            [self.tag1.id, self.tag3.id]
        )

        tgt3.position = 0
        tgt3.save()

        self.assertEqual(
            self.tg.ordered_tag_ids,
            [self.tag3.id, self.tag1.id]
        )

        self.tg.tags.clear()
        self.assertEqual(self.tg.ordered_tag_ids, [])

    def test_ordered_tags_returns_same_tags_as_ordered_tag_ids(self):
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag3, position=0)
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag1, position=1)

        ids_by_ordered_tags = list(self.tg.ordered_tags.values_list('id', flat=True))
        self.assertEqual(
            self.tg.ordered_tag_ids,
            ids_by_ordered_tags
        )

    # Tests for method update_tags
    def test_update_tags_adds_tags_and_orders_them(self):
        """Test that update_tags correctly adds and orders Tags."""
        self.tg.update_tags([self.tag3.id, self.tag1.id])

        tg_tags = list(TagGroupTag.objects.filter(tag_group=self.tg))
        self.assertEqual(
            [tag.tag_id for tag in tg_tags], [self.tag3.id, self.tag1.id]
        )
        self.assertEqual([tag.position for tag in tg_tags], [0, 1])

    def test_update_tags_corrects_position_gap(self):
        """Test that update_tags corrects position gaps."""
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag1, position=0)
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag2, position=2)
        positions_before = list(
            TagGroupTag.objects.filter(tag_group=self.tg).values_list(
                'position', flat=True
            )
        )
        self.assertEqual(positions_before, [0, 2])

        self.tg.update_tags([self.tag2.id, self.tag1.id])
        positions_after = list(
            TagGroupTag.objects.filter(tag_group=self.tg).values_list(
                'position', flat=True
            )
        )
        self.assertEqual(positions_after, [0, 1])

    def test_update_tags_removes_unlisted_tags(self):
        """Test that update_tags removes Tags not in the given list."""
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag1, position=0)
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag2, position=1)

        self.tg.update_tags([self.tag1.id])

        tg_tags = list(TagGroupTag.objects.filter(tag_group=self.tg))
        self.assertEqual(
            [tag.tag_id for tag in tg_tags], [self.tag1.id]
        )
        self.assertEqual([tag.position for tag in tg_tags], [0])

    def test_update_tags_reorders_existing_tags(self):
        """Test that update_tags changes the order of existing Tags."""
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag1, position=0)
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag2, position=1)

        self.tg.update_tags([self.tag2.id, self.tag1.id])

        tg_tags = list(TagGroupTag.objects.filter(tag_group=self.tg))
        self.assertEqual(
            [tag.tag_id for tag in tg_tags], [self.tag2.id, self.tag1.id]
        )
        self.assertEqual([tag.position for tag in tg_tags], [0, 1])

    def test_update_tags_idempotent_when_order_and_tags_unchanged(self):
        """Calling update_tags with the current order does not change anything."""
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag1, position=0)
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag2, position=1)

        self.tg.update_tags([self.tag1.id, self.tag2.id])

        tg_tags = list(TagGroupTag.objects.filter(tag_group=self.tg))
        self.assertEqual(
            [tag.tag_id for tag in tg_tags], [self.tag1.id, self.tag2.id]
        )
        self.assertEqual([tag.position for tag in tg_tags], [0, 1])

    def test_update_tags_combined_operation(self):
        """Test that add, remove and rearrange operations work together"""
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag1, position=0)
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag2, position=1)

        self.tag4 = Tag.objects.create(name='tag4')
        tag_ids_input = [self.tag3.id, self.tag1.id, self.tag4.id]

        self.tg.update_tags(tag_ids_input)

        tg_tags = list(TagGroupTag.objects.filter(tag_group=self.tg))
        self.assertEqual(
            [tag.tag_id for tag in tg_tags], tag_ids_input
        )
        self.assertEqual([tag.position for tag in tg_tags], [0, 1, 2])

    def test_update_tags_empty_list_clears_tags_from_post(self):
        """Test that an empty list removes tags from a TagGroup"""
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag1, position=0)
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag2, position=1)

        tag_ids_input = []
        self.tg.update_tags(tag_ids_input)

        tg_tags = list(TagGroupTag.objects.filter(tag_group=self.tg))

        self.assertEqual(
            [tag.tag_id for tag in tg_tags], tag_ids_input
        )

    def test_update_tags_duplicate_input(self):
        """Test that duplicated Tags in input don't cause inconsistencies"""
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag1, position=0)

        tag_ids_input = [
            self.tag1.id, self.tag2.id, self.tag2.id, self.tag3.id
        ]

        self.tg.update_tags(tag_ids_input)

        tg_tags = list(TagGroupTag.objects.filter(tag_group=self.tg))

        self.assertEqual(
            [tag.tag_id for tag in tg_tags],
            [self.tag1.id, self.tag2.id, self.tag3.id]
        )
        self.assertNotEqual(
            [tag.tag_id for tag in tg_tags], tag_ids_input
        )
        self.assertEqual([tag.position for tag in tg_tags], [0, 1, 2])

    def test_update_tags_invalid_tag_id(self):
        """Test invalid Tag raises an error"""
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag1, position=0)
        TagGroupTag.objects.create(tag_group=self.tg, tag=self.tag2, position=1)

        tag_ids_input = [self.tag1.id, self.tag2.id, 9999]
        with self.assertRaises(ValueError):
            self.tg.update_tags(tag_ids_input)

    def test_update_tags_transaction_rollback_on_error(self):
        from unittest.mock import patch

        self.tg.update_tags([self.tag1.id])
        original_tag_ids = self.tg.ordered_tag_ids

        # Patch bulk_create to raise error on second call
        with patch('posts.models.TagGroupTag.objects.bulk_create',
                   side_effect=Exception('DB error')):
            with self.assertRaises(Exception):
                self.tg.update_tags([self.tag1.id, self.tag2.id])

        self.tg.refresh_from_db()
        self.assertEqual(self.tg.ordered_tag_ids, original_tag_ids)


class TagModelTests(TestCase):
    """Test cases for a Tag model"""
    def test_str_representation(self):
        tag = Tag.objects.create(name='tag1')
        expected = f'#{tag.name}'
        self.assertEqual(str(tag), expected)

    def test_ordering_by_name(self):
        Tag.objects.create(name='tag1')
        Tag.objects.create(name='tag3')
        Tag.objects.create(name='tag2')
        tags = list(Tag.objects.all().values_list('name', flat=True))
        self.assertEqual(tags, ['tag1', 'tag2', 'tag3'])

    def test_tag_name_validation(self):
        """Test that tag names are validated"""
        from django.core.exceptions import ValidationError

        tag1 = Tag.objects.create(name='tag1')
        self.assertEqual(tag1.name, 'tag1')
        tag1.full_clean()

        tag2 = Tag.objects.create(name='tag2- ')
        with self.assertRaises(ValidationError):
            tag2.full_clean()

        tag3 = Tag.objects.create(name='')
        with self.assertRaises(ValidationError):
            tag3.full_clean()

        tag4 = Tag.objects.create(name='t.ag')
        with self.assertRaises(ValidationError):
            tag4.full_clean()

        tag5 = Tag.objects.create(name='😁')
        self.assertEqual(tag5.name, '😁')
        tag5.full_clean()

    def test_tag_uniqueness_case_insensitive(self):
        """Test that tag names are case-insensitive"""
        Tag.objects.create(name='Example')
        with self.assertRaises(IntegrityError):
            Tag.objects.create(name='example')

    def test_tag_name_max_length(self):
        """Test that tag names are limited to 64 characters"""
        from django.core.exceptions import ValidationError
        long_name = 'a' * 65
        tag = Tag(name=long_name)
        with self.assertRaises(ValidationError):
            tag.full_clean()


class TagGroupModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='user@example.com', password='pw')
        self.tag1 = Tag.objects.create(name='tag1')
        self.tag_group1 = TagGroup.objects.create(user=self.user, name='Tag Group')
        self.time_delta = 0.1
        self.longer_time_delta = 2 * self.time_delta

    def test_str_representation(self):
        self.assertEqual(str(self.tag_group1), 'Tag Group')

    def test_updated_at_on_creation(self):
        self.assertIsNotNone(self.tag_group1.updated_at)

    def test_updated_at_on_update(self):
        old_updated_at = self.tag_group1.updated_at
        time.sleep(self.longer_time_delta)
        self.tag_group1.name = 'New Name'
        self.tag_group1.save()
        self.assertNotAlmostEqual(
            self.tag_group1.updated_at.timestamp(),
            old_updated_at.timestamp(),
            delta=self.time_delta
        )

    def test_updated_at_on_add_tags(self):
        old_updated_at = self.tag_group1.updated_at
        time.sleep(self.longer_time_delta)
        self.tag_group1.update_tags([self.tag1.id])
        self.assertNotAlmostEqual(
            self.tag_group1.updated_at.timestamp(),
            old_updated_at.timestamp(),
            delta=self.time_delta
        )

    def test_updated_at_on_remove_tags(self):
        self.tag_group1.update_tags([self.tag1.id])
        old_updated_at = self.tag_group1.updated_at
        time.sleep(self.longer_time_delta)
        self.tag_group1.update_tags([])
        self.assertNotAlmostEqual(
            self.tag_group1.updated_at.timestamp(),
            old_updated_at.timestamp(),
            delta=self.time_delta
        )

    def test_updated_at_on_repeated_operation(self):
        """Test that updated_at is not updated when operation didn't cause changes"""
        self.tag_group1.update_tags([self.tag1.id])
        old_updated_at = self.tag_group1.updated_at
        time.sleep(self.longer_time_delta)
        self.tag_group1.update_tags([self.tag1.id])
        self.assertAlmostEqual(
            self.tag_group1.updated_at.timestamp(),
            old_updated_at.timestamp(),
            delta=self.time_delta
        )

    def test_tag_group_name_uniqueness(self):
        """Test that tag group names are unique per user"""
        with self.assertRaises(IntegrityError):
            TagGroup.objects.create(user=self.user, name='Tag Group')

    def test_tag_group_name_can_repeat_for_different_users(self):
        """Test that two different users can use the same tag group name"""
        self.assertTrue(
            TagGroup.objects.filter(user=self.user, name='Tag Group').exists()
        )

        another_user = User.objects.create_user(
            email='another@example.com', password='pw'
        )

        TagGroup.objects.create(user=another_user, name='Tag Group')

        self.assertEqual(TagGroup.objects.filter(name='Tag Group').count(), 2)
        self.assertEqual(TagGroup.objects.filter(user=self.user).count(), 1)
        self.assertEqual(TagGroup.objects.filter(user=another_user).count(), 1)


class MixinTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='u@example.com', password='pw')
        self.post = Post.objects.create(
            user=self.user, title='Test Post', description='Test Post Description'
        )
        self.tg = TagGroup.objects.create(user=self.user, name='Test')
        self.tg_tag1 = Tag.objects.create(name='tg_tag1')
        self.tg_tag2 = Tag.objects.create(name='tg_tag2')
        self.post_tag1 = Tag.objects.create(name='post_tag1')
        self.post_tag2 = Tag.objects.create(name='post_tag2')

        self.post.update_tags([self.post_tag1.id, self.post_tag2.id])
        self.tg.update_tags([self.tg_tag1.id, self.tg_tag2.id])

        self.other_user = User.objects.create_user(email='other@example.com')
        self.other_post = Post.objects.create(
            user=self.other_user, title='Other Test Post', description='Other User Post'
        )
        self.other_tag1 = Tag.objects.create(name='other_tag1')
        self.other_post.update_tags([self.other_tag1.id])

    def test_copy_tags_between_instances(self):
        self.assertEqual(self.tg.tags.count(), 2)
        self.assertEqual(self.post.tags.count(), 2)

        self.tg.copy_tags_from_other_instance(self.post)
        self.assertEqual(self.tg.tags.count(), 4)

        self.post.copy_tags_from_other_instance(self.tg)
        self.assertEqual(self.tg.tags.count(), 4)

    def test_copy_tags_in_order(self):
        """Test that tags are copied in the order they appear in the source instance"""
        old_tg_tags_list = self.tg.ordered_tag_ids
        old_post_tags_list = self.post.ordered_tag_ids

        self.tg.copy_tags_from_other_instance(self.post)
        self.assertEqual(
            self.tg.ordered_tag_ids, old_tg_tags_list + old_post_tags_list
        )

        self.post.copy_tags_from_other_instance(self.tg)
        self.assertEqual(
            self.post.ordered_tag_ids, old_post_tags_list + old_tg_tags_list
        )

    def test_idempotent_copy_tags(self):
        """Test that repeated operation changes nothing"""
        self.tg.copy_tags_from_other_instance(self.post)

        new_tg_tags_list = self.tg.ordered_tag_ids
        new_updated_at = self.tg.updated_at

        self.tg.copy_tags_from_other_instance(self.post)
        self.assertEqual(
            self.tg.ordered_tag_ids, new_tg_tags_list
        )

        self.assertEqual(
            self.tg.updated_at, new_updated_at
        )

    def test_empty_copy_tags(self):
        """Test that empty copy operation doesn't change anything"""
        old_updated_at = self.tg.updated_at
        old_tg_tags_list = self.tg.ordered_tag_ids
        empty_post = Post.objects.create(
            user=self.user, title='Empty Test Post', description='Empty Test Post'
        )
        self.tg.copy_tags_from_other_instance(empty_post)

        self.assertEqual(
            self.tg.ordered_tag_ids, old_tg_tags_list
        )
        self.assertEqual(
            self.tg.updated_at, old_updated_at
        )

    def test_copy_tags_between_two_posts(self):
        """Test that tags are copied between two posts"""
        new_post = Post.objects.create(
            user=self.user, title='New Test Post', description='New Test Post'
        )
        new_post_tag = Tag.objects.create(name='new_post_tag')
        new_post.update_tags([new_post_tag.id])
        self.post.copy_tags_from_other_instance(new_post)

        expected_post_tags_list = [self.post_tag1.id, self.post_tag2.id, new_post_tag.id]

        self.assertEqual(
            self.post.ordered_tag_ids, expected_post_tags_list
        )

    def test_copy_tags_from_another_user_instance(self):
        """Test that tags copying tags from another user instance raises an error"""
        with self.assertRaises(PermissionError):
            self.post.copy_tags_from_other_instance(self.other_post)


class SignalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='u@example.com', password='pw')
        self.post = Post.objects.create(
            user=self.user, title='Test Post', description='Test Post Description'
        )
        self.tg = TagGroup.objects.create(user=self.user, name='Test TagGroup')
        self.tg_tag1 = Tag.objects.create(name='tg_tag1')
        self.tg_tag2 = Tag.objects.create(name='tg_tag2')
        self.post_tag1 = Tag.objects.create(name='post_tag1')
        self.post_tag2 = Tag.objects.create(name='post_tag2')

        self.post.update_tags([self.post_tag1.id, self.post_tag2.id])
        self.tg.update_tags([self.tg_tag1.id, self.tg_tag2.id])

        self.time_delta = 0.1
        self.longer_time_delta = 2 * self.time_delta

    def test_delete_tag_group_deletes_orphaned_tags(self):
        self.assertTrue(TagGroup.objects.filter(name='Test TagGroup').exists())
        self.assertEqual(self.tg.tags.count(), 2)

        tag_ids = self.tg.ordered_tag_ids
        self.assertEqual(Tag.objects.filter(id__in=tag_ids).count(), 2)
        self.assertTrue(Tag.objects.filter(name='tg_tag1').exists())
        self.assertTrue(Tag.objects.filter(name='tg_tag2').exists())

        self.tg.delete()

        self.assertFalse(TagGroup.objects.filter(name='Test TagGroup').exists())
        self.assertEqual(Tag.objects.filter(id__in=tag_ids).count(), 0)
        self.assertFalse(Tag.objects.filter(name='tg_tag1').exists())
        self.assertFalse(Tag.objects.filter(name='tg_tag2').exists())

    def test_delete_post_deletes_orphaned_tags(self):
        self.assertTrue(Post.objects.filter(title='Test Post').exists())
        self.assertEqual(self.post.tags.count(), 2)

        tag_ids = self.post.ordered_tag_ids

        self.assertEqual(Tag.objects.filter(id__in=tag_ids).count(), 2)
        self.assertTrue(Tag.objects.filter(name='post_tag1').exists())
        self.assertTrue(Tag.objects.filter(name='post_tag2').exists())

        self.post.delete()

        self.assertFalse(Post.objects.filter(title='Test Post').exists())
        self.assertEqual(Tag.objects.filter(id__in=tag_ids).count(), 0)
        self.assertFalse(Tag.objects.filter(name='post_tag1').exists())
        self.assertFalse(Tag.objects.filter(name='post_tag2').exists())


class PostModelTests(TestCase):
    """Tests for a Post model"""
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='pw')
        self.post = Post.objects.create(user=self.user, title='Test Post')
        self.time_delta = 0.1
        self.longer_time_delta = 2 * self.time_delta

    def test_str_representation(self):
        self.assertEqual(str(self.post), 'Test Post')

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
        self.post.title = 'New Title'
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
        tag = Tag.objects.create(name='tag1')
        self.post.update_tags([tag.id])

        self.assertNotAlmostEqual(
            self.post.updated_at.timestamp(),
            old_updated_at.timestamp(),
            delta=self.time_delta
        )

    def test_updating_tag_without_changes_does_not_update_updated_at(self):
        tag = Tag.objects.create(name='tag1')
        self.post.update_tags([tag.id])

        old_updated_at = self.post.updated_at
        time.sleep(self.longer_time_delta)

        self.post.update_tags([tag.id])
        self.assertAlmostEqual(
            self.post.updated_at.timestamp(),
            old_updated_at.timestamp(),
            delta=self.time_delta
        )


class PostClearTagsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='pw')
        self.this_post = Post.objects.create(user=self.user, title='this_post')
        self.other_post = Post.objects.create(user=self.user, title='other_post')

        self.other_tg = TagGroup.objects.create(user=self.user, name='other_tg')

        # Tags
        self.tag_this_post = Tag.objects.create(name='this_post_only')
        self.tag_other_post = Tag.objects.create(name='other_post_only')
        self.tag_both_posts = Tag.objects.create(name='this_and_other_posts')
        self.tag_this_post_other_tg = Tag.objects.create(name='this_post_and_tg')
        self.tag_other_tg = Tag.objects.create(name='tg_only')
        self.tag_unrelated = Tag.objects.create(name='unrelated')

        # Attach tags to this_post
        self.this_post.update_tags(
            [self.tag_this_post.id,
             self.tag_both_posts.id,
             self.tag_this_post_other_tg.id]
        )

        # Attach tags to other_post
        self.other_post.update_tags([self.tag_both_posts.id, self.tag_other_post.id])

        # Attach tags to other_tg
        self.other_tg.update_tags([self.tag_other_tg.id, self.tag_this_post_other_tg.id])

    def test_clear_tags_deletes_exclusive_tag(self):
        self.this_post.clear_tags()
        self.assertFalse(Tag.objects.filter(id=self.tag_this_post.id).exists(),
                         "Tag used only by this post should be deleted")

    def test_clear_tags_does_not_delete_shared_tag(self):
        self.this_post.clear_tags()
        self.assertTrue(Tag.objects.filter(id=self.tag_both_posts.id).exists(),
                        "Tag used by multiple posts should NOT be deleted")

    def test_clear_tags_does_not_delete_tag_used_by_a_tag_group(self):
        self.this_post.clear_tags()
        self.assertTrue(Tag.objects.filter(id=self.tag_this_post_other_tg.id).exists(),
                        "Tag used by group should NOT be deleted")

    def test_unrelated_tags_survive(self):
        self.this_post.clear_tags()
        self.assertTrue(Tag.objects.filter(id=self.tag_unrelated.id).exists())
        self.assertTrue(Tag.objects.filter(id=self.tag_other_tg.id).exists())
        self.assertTrue(Tag.objects.filter(id=self.tag_other_post.id).exists())

    def test_clear_tags_idempotency(self):
        self.this_post.clear_tags()
        tags_before_clear = Tag.objects.count()
        self.this_post.clear_tags()
        self.assertEqual(Tag.objects.count(), tags_before_clear,
                         "Extra Tags should not be deleted on second call"
                         )

    def test_no_tags_deleted_if_none_match_criteria(self):
        tags_before_clear = Tag.objects.count()
        # Detach all tags from this_post
        self.this_post.update_tags([])
        self.this_post.clear_tags()
        # All tags still there
        self.assertTrue(Tag.objects.filter(id=self.tag_this_post_other_tg.id).exists())
        self.assertTrue(Tag.objects.filter(id=self.tag_both_posts.id).exists())
        self.assertTrue(Tag.objects.filter(id=self.tag_other_tg.id).exists())
        self.assertTrue(Tag.objects.filter(id=self.tag_unrelated.id).exists())
        self.assertTrue(Tag.objects.filter(id=self.tag_other_post.id).exists())

        self.assertEqual(Tag.objects.count(), tags_before_clear)


class TagGroupClearTagsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test2@example.com', password='pw')
        self.other_post = Post.objects.create(user=self.user, title='Test Post')

        self.this_tg = TagGroup.objects.create(user=self.user, name='this_tg')
        self.other_tg = TagGroup.objects.create(user=self.user, name='other_tg')

        # Tags
        self.tag_this_tg_only = Tag.objects.create(name='this_tg_only')
        self.tag_other_tg_only = Tag.objects.create(name='other_tg_only')
        self.tag_both_tgs = Tag.objects.create(name='this_and_other_tgs')
        self.tag_this_tg_other_post = Tag.objects.create(name='this_tg_and_post')
        self.tag_other_post = Tag.objects.create(name='post_only')
        self.tag_unrelated = Tag.objects.create(name='unrelated')

        # Attach tags to this_tg
        self.this_tg.update_tags([
            self.tag_this_tg_only.id,
            self.tag_both_tgs.id,
            self.tag_this_tg_other_post.id
        ])

        # Attach tags to other_tg
        self.other_tg.update_tags([self.tag_both_tgs.id, self.tag_other_tg_only.id])

        # Attach tags to other_post
        self.other_post.update_tags(
            [self.tag_other_post.id, self.tag_this_tg_other_post.id]
        )

    def test_clear_tags_deletes_exclusive_tag(self):
        self.this_tg.clear_tags()
        self.assertFalse(Tag.objects.filter(id=self.tag_this_tg_only.id).exists(),
                         "Tag used only by this tg should be deleted")

    def test_clear_tags_does_not_delete_shared_tag(self):
        self.this_tg.clear_tags()
        self.assertTrue(Tag.objects.filter(id=self.tag_both_tgs.id).exists(),
                        "Tag used by multiple tgs should NOT be deleted")

    def test_clear_tags_does_not_delete_tag_used_by_a_tag_group(self):
        self.this_tg.clear_tags()
        self.assertTrue(Tag.objects.filter(id=self.tag_this_tg_other_post.id).exists(),
                        "Tag used by post should NOT be deleted")

    def test_unrelated_tags_survive(self):
        self.this_tg.clear_tags()
        self.assertTrue(Tag.objects.filter(id=self.tag_unrelated.id).exists())
        self.assertTrue(Tag.objects.filter(id=self.tag_other_tg_only.id).exists())
        self.assertTrue(Tag.objects.filter(id=self.tag_other_post.id).exists())

    def test_clear_tags_idempotency(self):
        self.this_tg.clear_tags()
        tags_before_clear = Tag.objects.count()
        self.this_tg.clear_tags()
        self.assertEqual(Tag.objects.count(), tags_before_clear,
                         "Extra Tags should not be deleted on second call"
                         )

    def test_no_tags_deleted_if_none_match_criteria(self):
        tags_before_clear = Tag.objects.count()
        # Detach all tags from this_tg
        self.this_tg.tags.clear()
        self.this_tg.clear_tags()
        # All tags still there
        self.assertTrue(Tag.objects.filter(id=self.tag_this_tg_other_post.id).exists())
        self.assertTrue(Tag.objects.filter(id=self.tag_both_tgs.id).exists())
        self.assertTrue(Tag.objects.filter(id=self.tag_other_tg_only.id).exists())
        self.assertTrue(Tag.objects.filter(id=self.tag_unrelated.id).exists())
        self.assertTrue(Tag.objects.filter(id=self.tag_other_post.id).exists())

        self.assertEqual(Tag.objects.count(), tags_before_clear)


class UniqueConstraintOnCreationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test_unique@example.com')

    def test_unique_constraint_on_tg_creation(self):
        """
        Test that a tag group cannot be created with the same name as another tag group
        """
        TagGroup.objects.create(user=self.user, name='Tag Group')
        with self.assertRaises(IntegrityError):
            TagGroup.objects.create(user=self.user, name='Tag Group')

    def test_automatic_naming_dont_raise_errors(self):
        """
        Test that automatic naming works when the name is not provided
        Names should follow the pattern "Untitled TagGroup {number}"
            even if there are other TagGroups with that name
        """
        TagGroup.objects.create(user=self.user, name='Untitled TagGroup 2')
        TagGroup.objects.create(user=self.user)  # Untitled TagGroup 1
        TagGroup.objects.create(user=self.user)  # Untitled TagGroup 3

        self.assertEqual(TagGroup.objects.count(), 3)
        self.assertTrue(TagGroup.objects.filter(name='Untitled TagGroup 1').exists())
        self.assertTrue(TagGroup.objects.filter(name='Untitled TagGroup 3').exists())
