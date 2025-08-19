from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from allauth.socialaccount.models import SocialAccount, SocialApp
from posts.models import Tag, TagGroup, Post, PostTag
from django.contrib.messages import get_messages


User = get_user_model()


class DeleteAccountTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create user
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            profile_picture='https://example.com/pic.jpg'
        )

        # Create another user to verify their data is not affected
        self.other_user = User.objects.create_user(
            email='other@example.com',
            full_name='Other User'
        )

        # Create social app (required for SocialAccount)
        self.social_app = SocialApp.objects.create(
            provider='google',
            name='Google',
            client_id='test_client_id',
            secret='test_secret',
        )

        # Create social account for the user
        self.social_account = SocialAccount.objects.create(
            user=self.user,
            provider='google',
            uid='123456789',
            extra_data={'name': 'Test User'}
        )

        # Create social account for other user
        self.other_social_account = SocialAccount.objects.create(
            user=self.other_user,
            provider='google',
            uid='987654321',
            extra_data={'name': 'Other User'}
        )

        # Create tags
        self.tg_tag = Tag.objects.create(name='tg_tag')
        self.post_tag = Tag.objects.create(name='post_tag')
        self.shared_tag = Tag.objects.create(name='shared')
        self.orphan_tag = Tag.objects.create(name='orphan')

        # Create TagGroups
        self.user_taggroup = TagGroup.objects.create(
            user=self.user,
            name='My TagGroup'
        )
        self.user_taggroup.update_tags([self.tg_tag.id, self.orphan_tag.id])

        self.other_user_taggroup = TagGroup.objects.create(
            user=self.other_user,
            name='Other TagGroup'
        )
        self.other_user_taggroup.update_tags([self.shared_tag.id])

        # Create Posts
        self.user_post = Post.objects.create(
            user=self.user,
            title='My Post',
            description='My post description'
        )
        self.user_post.update_tags([self.post_tag.id, self.shared_tag.id])

        self.other_user_post = Post.objects.create(
            user=self.other_user,
            title='Other Post',
            description='Other post description'
        )
        self.other_user_post.update_tags([self.shared_tag.id])

        # Store initial counts for verification
        self.initial_user_count = User.objects.count()
        self.initial_tag_count = Tag.objects.count()
        self.initial_taggroup_count = TagGroup.objects.count()
        self.initial_post_count = Post.objects.count()
        self.initial_posttag_count = PostTag.objects.count()
        self.initial_social_account_count = SocialAccount.objects.count()

    def test_delete_account_requires_login(self):
        """Test that delete_account view requires authentication"""
        response = self.client.post(reverse('delete_account'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        # User should still exist
        self.assertTrue(User.objects.filter(email='test@example.com').exists())

    def test_delete_account_requires_post_method(self):
        """Test that delete_account view only accepts POST requests"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('delete_account'))
        self.assertEqual(response.status_code, 405)  # Method not allowed
        # User should still exist
        self.assertTrue(User.objects.filter(email='test@example.com').exists())

    def test_successful_account_deletion(self):
        """Test successful account deletion removes all user data"""
        self.client.force_login(self.user)

        response = self.client.post(reverse('delete_account'))

        # Should redirect to profile page
        self.assertRedirects(response, reverse('profile'))

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('successfully deleted', str(messages[0]))

        # User should be deleted
        self.assertFalse(User.objects.filter(email='test@example.com').exists())
        self.assertEqual(User.objects.count(), self.initial_user_count - 1)

        # User should be logged out (check via follow redirect)
        response = self.client.get(reverse('profile'))
        self.assertContains(response, 'You are not signed in')

    def test_user_social_accounts_deleted(self):
        """Test that user's social accounts are deleted"""
        self.client.force_login(self.user)

        # Verify social account exists before deletion
        self.assertTrue(SocialAccount.objects.filter(user=self.user).exists())

        self.client.post(reverse('delete_account'))

        # User's social account should be deleted
        self.assertFalse(SocialAccount.objects.filter(user=self.user).exists())
        # Other user's social account should remain
        self.assertTrue(SocialAccount.objects.filter(user=self.other_user).exists())
        self.assertEqual(
            SocialAccount.objects.count(),
            self.initial_social_account_count - 1
        )

    def test_user_posts_deleted(self):
        """Test that user's posts are deleted"""
        self.client.force_login(self.user)

        # Verify post exists before deletion
        self.assertTrue(Post.objects.filter(user=self.user).exists())

        self.client.post(reverse('delete_account'))

        # User's posts should be deleted
        self.assertFalse(Post.objects.filter(user=self.user).exists())
        # Other user's posts should remain
        self.assertTrue(Post.objects.filter(user=self.other_user).exists())
        self.assertEqual(Post.objects.count(), self.initial_post_count - 1)

    def test_user_taggroups_deleted(self):
        """Test that user's tag groups are deleted"""
        self.client.force_login(self.user)

        # Verify taggroup exists before deletion
        self.assertTrue(TagGroup.objects.filter(user=self.user).exists())

        self.client.post(reverse('delete_account'))

        # User's taggroups should be deleted
        self.assertFalse(TagGroup.objects.filter(user=self.user).exists())
        # Other user's taggroups should remain
        self.assertTrue(TagGroup.objects.filter(user=self.other_user).exists())
        self.assertEqual(TagGroup.objects.count(), self.initial_taggroup_count - 1)

    def test_posttags_deleted_with_posts(self):
        """Test that PostTag relationships are deleted with posts"""
        self.client.force_login(self.user)

        # Verify PostTags exist for user's post
        user_posttags = PostTag.objects.filter(post__user=self.user)
        self.assertTrue(user_posttags.exists())
        initial_user_posttags_count = user_posttags.count()

        self.client.post(reverse('delete_account'))

        # User's PostTags should be deleted
        self.assertFalse(PostTag.objects.filter(post__user=self.user).exists())
        # Other user's PostTags should remain
        self.assertTrue(PostTag.objects.filter(post__user=self.other_user).exists())
        self.assertEqual(
            PostTag.objects.count(),
            self.initial_posttag_count - initial_user_posttags_count
        )

    def test_orphaned_tags_cleanup(self):
        """Test that orphaned tags are cleaned up during deletion"""
        self.client.force_login(self.user)

        # Before deletion: verify tags exist
        self.assertTrue(Tag.objects.filter(name='tg_tag').exists())
        self.assertTrue(Tag.objects.filter(name='post_tag').exists())
        self.assertTrue(Tag.objects.filter(name='orphan').exists())
        self.assertTrue(Tag.objects.filter(name='shared').exists())

        self.client.post(reverse('delete_account'))

        # After deletion: orphaned tags should be deleted, shared tags should remain
        self.assertFalse(Tag.objects.filter(name='tg_tag').exists(),
                         "Tag used only by deleted user's taggroup should be deleted")
        self.assertFalse(Tag.objects.filter(name='post_tag').exists(),
                         "Tag used only by deleted user's post should be deleted")
        self.assertFalse(Tag.objects.filter(name='orphan').exists(),
                         "Orphaned tag should be deleted")
        self.assertTrue(Tag.objects.filter(name='shared').exists(),
                        "Shared tag should remain")

        # Verify final tag count
        expected_remaining_tags = 1  # Only 'shared' tag should remain
        self.assertEqual(Tag.objects.count(), expected_remaining_tags)

    def test_other_users_data_unaffected(self):
        """Test that other users' data is not affected by account deletion"""
        self.client.force_login(self.user)

        # Store other user's data references
        other_user_id = self.other_user.id
        other_post_id = self.other_user_post.id
        other_taggroup_id = self.other_user_taggroup.id
        other_social_account_id = self.other_social_account.id

        self.client.post(reverse('delete_account'))

        # Other user should still exist
        self.assertTrue(User.objects.filter(id=other_user_id).exists())

        # Other user's data should still exist
        self.assertTrue(Post.objects.filter(id=other_post_id).exists())
        self.assertTrue(TagGroup.objects.filter(id=other_taggroup_id).exists())
        self.assertTrue(
            SocialAccount.objects.filter(id=other_social_account_id).exists()
        )

        # Other user's data should be intact
        other_user = User.objects.get(id=other_user_id)
        self.assertEqual(other_user.email, 'other@example.com')
        self.assertEqual(other_user.posts.count(), 1)
        self.assertEqual(other_user.tag_groups.count(), 1)

    def test_cascade_deletion_signals_triggered(self):
        """Test that the pre_delete signals are triggered for tag cleanup"""
        self.client.force_login(self.user)

        # This test verifies that the signals work by checking the end result
        # If signals weren't triggered, orphaned tags would remain

        expected_to_remain = {'shared'}  # Only tag used by other user
        expected_to_be_deleted = {'tg_tag', 'post_tag', 'orphan'}

        self.client.post(reverse('delete_account'))

        tags_after = set(Tag.objects.values_list('name', flat=True))

        # Verify expected tags were deleted
        for tag_name in expected_to_be_deleted:
            self.assertNotIn(
                tag_name,
                tags_after,
                f"Tag '{tag_name}' should have been deleted"
            )

        # Verify expected tags remained
        for tag_name in expected_to_remain:
            self.assertIn(tag_name, tags_after, f"Tag '{tag_name}' should have remained")
