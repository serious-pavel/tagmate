from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth import get_user_model
from io import StringIO
from posts.models import Tag, Post, TagGroup

User = get_user_model()


class ClearOrphanedTagsCommandTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='testuser@example.com')

        self.orphaned_tag = Tag.objects.create(name='orphaned')
        self.post_tag = Tag.objects.create(name='used_by_post')
        self.tg_tag = Tag.objects.create(name='used_by_taggroup')
        self.shared_tag = Tag.objects.create(name='shared')

        self.post = Post.objects.create(
            user=self.user,
            title='Test Post',
            description='Test'
        )
        self.post.update_tags([self.post_tag.id, self.shared_tag.id])

        self.tag_group = TagGroup.objects.create(
            user=self.user,
            name='Test Group'
        )
        self.tag_group.tags.add(self.tg_tag, self.shared_tag)

    def test_deletes_orphaned_tags_only(self):
        """Test that only truly orphaned tags are deleted"""
        # Verify initial state
        self.assertEqual(Tag.objects.count(), 4)

        # Run command
        out = StringIO()
        call_command('clear_orphaned_tags', stdout=out)

        # Only orphaned tag should be deleted
        self.assertEqual(Tag.objects.count(), 3)
        self.assertFalse(Tag.objects.filter(name='orphaned').exists())
        self.assertTrue(Tag.objects.filter(name='used_by_post').exists())
        self.assertTrue(Tag.objects.filter(name='used_by_taggroup').exists())
        self.assertTrue(Tag.objects.filter(name='shared').exists())

        self.assertIn('Successfully deleted 1 orphaned tags', out.getvalue())

    def test_dry_run_doesnt_delete(self):
        """Test that dry run shows what would be deleted without deleting"""
        initial_count = Tag.objects.count()

        out = StringIO()
        call_command('clear_orphaned_tags', '--dry-run', stdout=out)

        # Nothing should be deleted
        self.assertEqual(Tag.objects.count(), initial_count)
        self.assertIn('Would delete 1 orphaned tags', out.getvalue())

    def test_no_orphaned_tags(self):
        """Test behavior when no orphaned tags exist"""
        # Delete the orphaned tag manually
        self.orphaned_tag.delete()

        out = StringIO()
        call_command('clear_orphaned_tags', stdout=out)

        self.assertIn('No orphaned tags found', out.getvalue())

    def test_verbose_output(self):
        """Test that verbose output shows tag names"""
        out = StringIO()
        call_command('clear_orphaned_tags', '--dry-run', verbosity=2, stdout=out)

        output = out.getvalue()
        self.assertIn('Orphaned tags: orphaned', output)

    def test_multiple_orphaned_tags(self):
        """Test handling multiple orphaned tags"""
        Tag.objects.create(name='orphaned2')
        Tag.objects.create(name='orphaned3')

        out = StringIO()
        call_command('clear_orphaned_tags', stdout=out)

        # Should delete 3 orphaned tags total
        self.assertIn('Successfully deleted 3 orphaned tags', out.getvalue())
        self.assertEqual(Tag.objects.count(), 3)
