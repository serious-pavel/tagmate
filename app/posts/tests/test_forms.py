from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from posts.models import Post, Tag, TagGroup, PostTag

User = get_user_model()


class PostFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='form_tester@example.com')
        # Login a user with social auth
        self.client.force_login(self.user)

        self.post = Post.objects.create(
            user=self.user,
            title="Test forms post",
            description="Post for testing forms"
        )

        self.tg = TagGroup.objects.create(
            user=self.user,
            name="Test forms TG",
        )

    def test_add_valid_tag(self):
        url = reverse('post_editor', args=[self.post.pk])
        data = {'tags_to_attach': 'sometag', 'action': 'post_attach_tags'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Tag.objects.filter(name='sometag').exists())
        self.assertContains(response, "sometag")

    def test_invalid_tag_shows_error(self):
        url = reverse('post_editor', args=[self.post.pk])
        data = {'tags_to_attach': '!!invalidtag!!', 'action': 'post_attach_tags'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hashtags may only contain ")
        self.assertFalse(Tag.objects.filter(name='!!invalidtag!!').exists())
