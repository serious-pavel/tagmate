from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from bs4 import BeautifulSoup

from posts.models import Post, Tag, TagGroup, PostTag

User = get_user_model()
POST_TAG_LIST_ID = 'dnd-list-post'
POST_ADD_INPUT_ID = 'post-tags-to-attach'


def tag_in_list(response, tag_name, parent_id):
    """
    Check if Tag is in the list of tags attached to the Post.
    Tag is expected to be in the div with id = parent_id.
    Tag is expected to be a <div class="tag"> with text = tag_name.
    """
    soup = BeautifulSoup(response.content, 'html.parser')
    tag_list = soup.find('div', id=parent_id)
    if not tag_list:
        return False
    for div in tag_list.find_all('div', class_="tag"):
        if div.text.strip() == tag_name:
            return True
    return False


def input_is_prefilled(response, tag_name, input_id):
    """
    Returns True if the <input> with a given id is prefilled with tag_name as value.
    """
    soup = BeautifulSoup(response.content, 'html.parser')
    input_field = soup.find("input", {"id": input_id})
    return input_field is not None and input_field.get('value', '') == tag_name


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

    def test_add_valid_tag_only_post(self):
        url = reverse('post_editor', args=[self.post.pk])
        data = {'tags_to_attach': 'sometag', 'action': 'post_attach_tags'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Tag.objects.filter(name='sometag').exists())
        self.assertTrue(PostTag.objects.filter(
            post=self.post, tag=Tag.objects.get(name='sometag')
        ).exists())
        self.assertContains(response, "sometag")

        # Check client redirected to the same page
        # redirect_chain contains tuples of (url, status_code)
        self.assertIn((url, 302), response.redirect_chain)

    def test_add_valid_tag_post_tg(self):
        url = reverse('post_tg_editor', args=[self.post.pk, self.tg.pk])
        data = {'tags_to_attach': 'sometag2', 'action': 'post_attach_tags'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Tag.objects.filter(name='sometag2').exists())
        self.assertTrue(PostTag.objects.filter(
            post=self.post, tag=Tag.objects.get(name='sometag2')
        ).exists())
        self.assertContains(response, "sometag2")
        self.assertTrue(tag_in_list(response, 'sometag2', POST_TAG_LIST_ID))
        self.assertIn((url, 302), response.redirect_chain)
        self.assertFalse(input_is_prefilled(response, 'sometag2', POST_ADD_INPUT_ID))

    def test_invalid_tag_shows_error(self):
        url = reverse('post_editor', args=[self.post.pk])
        data = {'tags_to_attach': '!!invalidtag!!', 'action': 'post_attach_tags'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hashtags may only contain ")
        self.assertFalse(Tag.objects.filter(name='!!invalidtag!!').exists())

        self.assertFalse(PostTag.objects.filter(
            post=self.post, tag=Tag.objects.filter(name='!!invalidtag!!').first()
        ).exists())

        self.assertFalse(tag_in_list(response, '!!invalidtag!!', POST_TAG_LIST_ID))
        self.assertTrue(
            input_is_prefilled(response, '!!invalidtag!!', POST_ADD_INPUT_ID)
        )

