from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from bs4 import BeautifulSoup

from posts.models import Post, Tag, TagGroup

User = get_user_model()
POST_TAG_LIST_ID = 'dnd-list-post'
POST_ADD_INPUT_ID = 'post-tags-to-attach'
TG_TAG_LIST_ID = 'dnd-list-tg'
TG_ADD_INPUT_ID = 'tg-tags-to-attach'


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


def assert_tag_in_list(response, tag_name, parent_id):
    """
    Assert that a Tag with tag_name exists in a div with id=parent_id in the response.
    Raise AssertionError with a descriptive message if not found.
    """
    soup = BeautifulSoup(response.content, 'html.parser')
    tag_list = soup.find('div', id=parent_id)
    if not tag_list:
        raise AssertionError(
            f"Could not find tag list div with id '{parent_id}' in the response."
        )
    tag_divs = [div.text.strip() for div in tag_list.find_all('div', class_="tag")]
    if tag_name not in tag_divs:
        raise AssertionError(
            f"Tag '{tag_name}' was not found in <div id='{parent_id}'>. "
            f"Available tags: {tag_divs if tag_divs else '[none]'}"
        )


def assert_tag_not_in_list(response, tag_name, parent_id, msg=None):
    """
    Assert that a tag with the given name **is NOT present** in the list rendered in
    the div with id=parent_id.
    """
    soup = BeautifulSoup(response.content, 'html.parser')
    tag_list = soup.find('div', id=parent_id)
    if not tag_list:
        # If the tag list doesn't even exist, then the tag is definitely not present.
        return
    tag_divs = [div.text.strip() for div in tag_list.find_all('div', class_="tag")]
    if tag_name in tag_divs:
        raise AssertionError(
            msg or (
                f"Did NOT expect tag '{tag_name}' in <div id='{parent_id}'>, "
                f"but found these tags: {tag_divs}"
            )
        )


def input_is_prefilled(response, tag_name, input_id):
    """
    Returns True if the <input> with a given id is prefilled with tag_name as value.
    """
    soup = BeautifulSoup(response.content, 'html.parser')
    input_field = soup.find("input", {"id": input_id})
    return input_field is not None and input_field.get('value', '') == tag_name


class TagFormsTests(TestCase):
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

        self.tag_in_post = Tag.objects.create(name="attached_to_post")
        self.tag_in_tg = Tag.objects.create(name="attached_to_tg")
        self.tag_in_both = Tag.objects.create(name="attached_to_both")

        self.post.update_tags([self.tag_in_post.id, self.tag_in_both.id])
        self.tg.tags.add(self.tag_in_tg.id)

    def assert_valid_tag_add(self, url, tag_name, action, tag_list_id, input_id):
        """
        Helper for asserting valid tag add scenario.
        """
        data = {'tags_to_attach': tag_name, 'action': action}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Tag.objects.filter(name=tag_name).exists())

        if action == 'post_attach_tags':
            self.assertTrue(
                Tag.objects.filter(name=tag_name, posts__title=self.post.title).exists()
            )
        elif action == 'tg_attach_tags':
            self.assertTrue(
                Tag.objects.filter(name=tag_name, tag_groups__name=self.tg.name).exists()
            )

        self.assertNotContains(response, "Hashtags may only contain ")
        assert_tag_in_list(response, tag_name, tag_list_id)
        self.assertFalse(input_is_prefilled(response, tag_name, input_id))

        # Check client redirected to the same page
        # redirect_chain contains tuples of (url, status_code)
        self.assertIn((url, 302), response.redirect_chain)

    def assert_invalid_tag_add(self, url, tag_name, action, tag_list_id, input_id):
        """
        Helper for asserting invalid tag add scenario.
        """
        data = {'tags_to_attach': tag_name, 'action': action}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hashtags may only contain ")
        self.assertFalse(Tag.objects.filter(name=tag_name).exists())
        assert_tag_not_in_list(response, tag_name, tag_list_id)

        self.assertTrue(input_is_prefilled(response, tag_name, input_id))

        # Input for another "Add Tags" field shouldn't be prefilled
        if input_id == POST_ADD_INPUT_ID:
            opposite_input_id = TG_ADD_INPUT_ID
        else:
            opposite_input_id = POST_ADD_INPUT_ID

        self.assertFalse(input_is_prefilled(response, tag_name, opposite_input_id))

    def assert_tag_detach(self, url, tag_id, action):
        """
        Helper for asserting Tag detaching scenario.
        """
        tag_name = Tag.objects.get(pk=tag_id).name
        if action == 'post_detach_tag':
            tag_list_id = POST_TAG_LIST_ID
            opposite_tag_list_id = TG_TAG_LIST_ID
        else:
            tag_list_id = TG_TAG_LIST_ID
            opposite_tag_list_id = POST_TAG_LIST_ID

        response_init = self.client.get(url, follow=True)
        self.assertEqual(response_init.status_code, 200)
        assert_tag_in_list(response_init, tag_name, tag_list_id)

        opposite_tag_state = tag_in_list(response_init, tag_name, opposite_tag_list_id)

        data = {'tag_to_detach': tag_id, 'action': action}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Tag.objects.filter(pk=tag_id).exists())

        assert_tag_not_in_list(response, tag_name, tag_list_id)
        # Detaching a Tag from one list shouldn't affect another list with Tags
        self.assertEqual(
            opposite_tag_state, tag_in_list(response, tag_name, opposite_tag_list_id)
        )

        self.assertIn((url, 302), response.redirect_chain)

    def test_post_add_valid_tag_on_post_page(self):
        """
        Test adding a valid tag to a post on a page with only post chosen.
        Link: /post/<post_pk>
        """
        url = reverse('post_editor', args=[self.post.pk])

        self.assert_valid_tag_add(
            url, 'sometag', 'post_attach_tags', POST_TAG_LIST_ID, POST_ADD_INPUT_ID
        )

    def test_post_add_valid_tag_on_post_tg_page(self):
        """
        Test adding a valid tag to a post on a page with post and TG chosen.
        Link: /post/<post_pk>/tg/<tg_pk>
        """
        url = reverse('post_tg_editor', args=[self.post.pk, self.tg.pk])

        self.assert_valid_tag_add(
            url, 'sometag2', 'post_attach_tags', POST_TAG_LIST_ID, POST_ADD_INPUT_ID
        )

    def test_post_add_invalid_tag_on_post_page(self):
        """
        Test adding an invalid tag to a post on a page with only post chosen.
        Link: /post/<post_pk>
        """
        url = reverse('post_editor', args=[self.post.pk])

        self.assert_invalid_tag_add(
            url, '!!invalidtag!!', 'post_attach_tags',
            POST_TAG_LIST_ID, POST_ADD_INPUT_ID
        )

    def test_post_add_invalid_tag_on_post_tg_page(self):
        """
        Test adding an invalid tag to a post on a page with post and TG chosen.
        Link: /post/<post_pk>/tg/<tg_pk>
        """
        url = reverse('post_tg_editor', args=[self.post.pk, self.tg.pk])

        self.assert_invalid_tag_add(
            url, '!!invalidtag2!!', 'post_attach_tags',
            POST_TAG_LIST_ID, POST_ADD_INPUT_ID
        )

    def test_tg_add_valid_tag_on_tg_page(self):
        """
        Test adding a valid tag to a TagGroup on a page with only Post chosen.
        Link: /tg/<tg_pk>
        """
        url = reverse('tg_editor', args=[self.tg.pk])

        self.assert_valid_tag_add(
            url, 'sometag3', 'tg_attach_tags', TG_TAG_LIST_ID, TG_ADD_INPUT_ID
        )

    def test_tg_add_valid_tag_on_post_tg_page(self):
        """
        Test adding a valid tag to a TagGroup on a page with Post and TG chosen.
        Link: /post/<post_pk>/tg/<tg_pk>
        """
        url = reverse('post_tg_editor', args=[self.post.pk, self.tg.pk])

        self.assert_valid_tag_add(
            url, 'sometag4', 'tg_attach_tags', TG_TAG_LIST_ID, TG_ADD_INPUT_ID
        )

    def test_tg_add_invalid_tag_on_tg_page(self):
        """
        Test adding a valid tag to a TagGroup on a page with only Post chosen.
        Link: /tg/<tg_pk>
        """
        url = reverse('tg_editor', args=[self.tg.pk])

        self.assert_invalid_tag_add(
            url, '!!invalidtag3!!', 'tg_attach_tags', TG_TAG_LIST_ID, TG_ADD_INPUT_ID
        )

    def test_tg_add_invalid_tag_on_post_tg_page(self):
        """
        Test adding a valid tag to a TagGroup on a page with Post and TG chosen.
        Link: /post/<post_pk>/tg/<tg_pk>
        """
        url = reverse('post_tg_editor', args=[self.post.pk, self.tg.pk])

        self.assert_invalid_tag_add(
            url, '!!invalidtag4!!', 'tg_attach_tags', TG_TAG_LIST_ID, TG_ADD_INPUT_ID
        )

    def test_post_detach_tag_attached_post_page(self):
        """
        Test detaching a Tag attached to a Post on a page with only Post chosen.
        Link: /post/<post_pk>
        """

        url = reverse('post_editor', args=[self.post.pk])
        self.assert_tag_detach(url, self.tag_in_post.id, 'post_detach_tag')
        self.assert_tag_detach(url, self.tag_in_both.id, 'post_detach_tag')

    def test_post_detach_tag_attached_post_tg_page(self):
        """
        Test detaching a Tag attached to a Post on a page with only Post chosen.
        Link: /post/<post_pk>/tg/<tg_pk>
        """

        url = reverse('post_tg_editor', args=[self.post.pk, self.tg.pk])
        self.assert_tag_detach(url, self.tag_in_post.id, 'post_detach_tag')
        self.assert_tag_detach(url, self.tag_in_both.id, 'post_detach_tag')
