from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.urls import resolve

from bs4 import BeautifulSoup

from posts.models import Post, Tag, TagGroup

User = get_user_model()
POST_TAG_LIST_ID = 'dnd-list-post'
POST_ADD_INPUT_ID = 'post-tags-to-attach'
TG_TAG_LIST_ID = 'dnd-list-tg'
TG_ADD_INPUT_ID = 'tg-tags-to-attach'


def get_tag_list(response, parent_id, child_class):
    """
    Return a list of tag names (stripped) inside a div with the given id in the response.
    Returns [] if container is missing.
    """
    soup = BeautifulSoup(response.content, 'html.parser')
    tag_list = soup.find('div', id=parent_id)
    if not tag_list:
        return []
    return [div.text.strip() for div in tag_list.find_all('div', class_=child_class)]


def assert_tag_in_list(response, tag_name, parent_id, child_class):
    tag_divs = get_tag_list(response, parent_id, child_class)
    if tag_name not in tag_divs:
        raise AssertionError(
            f"Expected tag '{tag_name}' in <div id='{parent_id}'>, "
            f"but only found: {tag_divs if tag_divs else '[none]'}"
        )


def assert_tag_not_in_list(response, tag_name, parent_id, child_class):
    tag_divs = get_tag_list(response, parent_id, child_class)
    if tag_name in tag_divs:
        raise AssertionError(
            f"Did NOT expect tag '{tag_name}' in <div id='{parent_id}'>, "
            f"but found these tags: {tag_divs}"
        )


def input_is_prefilled(response, tag_name, input_id):
    """
    Returns True if the <input> with a given id is prefilled with tag_name as value.
    """
    soup = BeautifulSoup(response.content, 'html.parser')
    input_field = soup.find("input", {"id": input_id})
    return input_field is not None and input_field.get('value', '') == tag_name


def extract_url(url_2):
    # Remove the domain part if present
    from urllib.parse import urlparse
    path = urlparse(url_2).path
    match = resolve(path)
    # match.kwargs contains a dictionary of args in url
    return match.kwargs


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
        self.tg.tags.add(self.tag_in_tg.id, self.tag_in_both.id)

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
        assert_tag_in_list(response, tag_name, tag_list_id, 'tag')
        self.assertFalse(input_is_prefilled(response, tag_name, input_id))

        # Check client redirected to the same page
        # redirect_chain contains tuples of (url, status_code)
        self.assertIn((url, 302), response.redirect_chain)

    def assert_invalid_tag_add(self, url, tag_name, action, tag_list_id, main_input_id):
        """
        Helper for asserting invalid tag add scenario.
        """
        data = {'tags_to_attach': tag_name, 'action': action}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hashtags may only contain ")
        self.assertFalse(Tag.objects.filter(name=tag_name).exists())
        assert_tag_not_in_list(response, tag_name, tag_list_id, 'tag')

        self.assertTrue(input_is_prefilled(response, tag_name, main_input_id))

        # Input for another "Add Tags" field shouldn't be prefilled
        if main_input_id == POST_ADD_INPUT_ID:
            other_input_id = TG_ADD_INPUT_ID
        else:
            other_input_id = POST_ADD_INPUT_ID

        self.assertFalse(input_is_prefilled(response, tag_name, other_input_id))

    def assert_tag_detach(self, url, tag_id, action):
        """
        Helper for asserting Tag detaching scenario.
        """
        tag_name = Tag.objects.get(pk=tag_id).name
        if action == 'post_detach_tag':
            main_tag_list_id = POST_TAG_LIST_ID
            other_tag_list_id = TG_TAG_LIST_ID
        else:
            main_tag_list_id = TG_TAG_LIST_ID
            other_tag_list_id = POST_TAG_LIST_ID

        response_init = self.client.get(url, follow=True)
        self.assertEqual(response_init.status_code, 200)
        assert_tag_in_list(response_init, tag_name, main_tag_list_id, 'tag')

        other_tag_list_before = get_tag_list(response_init, other_tag_list_id, 'tag')
        other_tag_state_before = tag_name in other_tag_list_before

        data = {'tag_to_detach': tag_id, 'action': action}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Tag.objects.filter(pk=tag_id).exists())

        assert_tag_not_in_list(response, tag_name, main_tag_list_id, 'tag')
        # Detaching a Tag from one list shouldn't affect another list with Tags
        other_tag_list_after = get_tag_list(response, other_tag_list_id, 'tag')
        other_tag_state_after = tag_name in other_tag_list_after
        self.assertEqual(
            other_tag_state_before, other_tag_state_after
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

    def test_post_detach_tag_on_post_page(self):
        """
        Test detaching a Tag attached to a Post on a page with only Post chosen.
        Link: /post/<post_pk>
        """

        url = reverse('post_editor', args=[self.post.pk])
        self.assert_tag_detach(url, self.tag_in_post.id, 'post_detach_tag')
        self.assert_tag_detach(url, self.tag_in_both.id, 'post_detach_tag')

    def test_post_detach_tag_on_post_tg_page(self):
        """
        Test detaching a Tag attached to a Post on a page with Post and TG chosen.
        Link: /post/<post_pk>/tg/<tg_pk>
        """

        url = reverse('post_tg_editor', args=[self.post.pk, self.tg.pk])
        self.assert_tag_detach(url, self.tag_in_post.id, 'post_detach_tag')
        self.assert_tag_detach(url, self.tag_in_both.id, 'post_detach_tag')

    def test_tg_detach_tag_on_tg_page(self):
        """
        Test detaching a Tag attached to a TagGroup on a page with only TG chosen.
        Link: /post/<post_pk>
        """

        url = reverse('tg_editor', args=[self.tg.pk])
        self.assert_tag_detach(url, self.tag_in_tg.id, 'tg_detach_tag')
        self.assert_tag_detach(url, self.tag_in_both.id, 'tg_detach_tag')

    def test_tg_detach_tag_on_post_tg_page(self):
        """
        Test detaching a Tag attached to a TagGroup on a page with Post and TG chosen.
        Link: /post/<post_pk>/tg/<tg_pk>
        """

        url = reverse('post_tg_editor', args=[self.post.pk, self.tg.pk])
        self.assert_tag_detach(url, self.tag_in_tg.id, 'tg_detach_tag')
        self.assert_tag_detach(url, self.tag_in_both.id, 'tg_detach_tag')


class CreateObjectsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='create_obj@example.com')
        self.client.force_login(self.user)

        self.post = Post.objects.create(
            user=self.user,
            title="Existing Post",
            description="Post for testing object creation"
        )

        self.tg = TagGroup.objects.create(
            user=self.user,
            name="Existing TG",
        )

    def assert_object_create(self, url, action):
        """
        Asserts that a new object is created when the given action is used.
        """
        url_args = extract_url(url)
        new_item_title = 'New Item Name'

        data = {'action': action}
        parent_id = None
        if action == 'create_post':
            data['new_post_title'] = new_item_title
            parent_id = 'recent-posts'
            self.assertFalse(
                Post.objects.filter(title=new_item_title, user=self.user).exists()
            )
        elif action == 'create_tg':
            data['new_tg_name'] = new_item_title
            parent_id = 'recent-tgs'
            self.assertFalse(
                TagGroup.objects.filter(name=new_item_title, user=self.user).exists()
            )

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        assert_tag_in_list(response, new_item_title, parent_id, 'list-item-title')

        response_url = response.request['PATH_INFO']
        self.assertIn((response_url, 302), response.redirect_chain)
        response_url_args = extract_url(response_url)

        if action == 'create_post':
            self.assertTrue(
                Post.objects.filter(title=new_item_title, user=self.user).exists()
            )
            self.assertIn('post_pk', response_url_args)

            new_post_pk = response_url_args['post_pk']
            self.assertEqual(
                Post.objects.get(title=new_item_title, user=self.user).pk, new_post_pk
            )

            if 'post_pk' in url_args:
                self.assertNotEqual(new_post_pk, url_args['post_pk'])

            if 'tg_pk' in url_args:
                self.assertEqual(response_url_args['tg_pk'], url_args['tg_pk'])

        if action == 'create_tg':
            self.assertTrue(
                TagGroup.objects.filter(name=new_item_title, user=self.user).exists()
            )
            self.assertIn('tg_pk', response_url_args)

            new_tg_pk = response_url_args['tg_pk']
            self.assertEqual(
                TagGroup.objects.get(name=new_item_title, user=self.user).pk, new_tg_pk
            )

            if 'tg_pk' in url_args:
                self.assertNotEqual(new_tg_pk, url_args['tg_pk'])

            if 'post_pk' in url_args:
                self.assertEqual(response_url_args['post_pk'], url_args['post_pk'])

    def test_post_create_on_empty_page(self):
        """
        Test creating a new Post on an empty page.
        Link: /
        """
        url = reverse('index')
        self.assert_object_create(url, 'create_post')

    def test_post_create_on_post_page(self):
        """
        Test creating a new Post on a page with only Post chosen.
        Link: /post/<post_pk>
        """
        url = reverse('post_editor', args=[self.post.pk])
        self.assert_object_create(url, 'create_post')

    def test_post_create_on_tg_page(self):
        """
        Test creating a new Post on a page with only TG chosen.
        Link: /tg/<tg_pk>
        """
        url = reverse('tg_editor', args=[self.tg.pk])
        self.assert_object_create(url, 'create_post')

    def test_post_create_on_post_tg_page(self):
        """
        Test creating a new post on a page with Post and TG chosen.
        Link: /post/<post_pk>/tg/<tg_pk>
        """
        url = reverse('post_tg_editor', args=[self.post.pk, self.tg.pk])
        self.assert_object_create(url, 'create_post')

    def test_tg_create_on_empty_page(self):
        """
        Test creating a new TagGroup on an empty page.
        Link: /
        """
        url = reverse('index')
        self.assert_object_create(url, 'create_tg')

    def test_tg_create_on_post_page(self):
        """
        Test creating a new TagGroup on a page with only Post chosen.
        Link: /post/<post_pk>
        """
        url = reverse('post_editor', args=[self.post.pk])
        self.assert_object_create(url, 'create_tg')

    def test_tg_create_on_tg_page(self):
        """
        Test creating a new TagGroup on a page with only TG chosen.
        Link: /tg/<tg_pk>
        """
        url = reverse('tg_editor', args=[self.tg.pk])
        self.assert_object_create(url, 'create_tg')

    def test_tg_create_on_post_tg_page(self):
        """
        Test creating a new TagGroup on a page with Post and TG chosen.
        Link: /post/<post_pk>/tg/<tg_pk>
        """
        url = reverse('post_tg_editor', args=[self.post.pk, self.tg.pk])
        self.assert_object_create(url, 'create_tg')


class DeleteObjectsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='delete_obj@example.com')
        self.client.force_login(self.user)

        self.post = Post.objects.create(
            user=self.user,
            title="Existing Post",
            description="Post for testing object creation"
        )

        self.tg = TagGroup.objects.create(
            user=self.user,
            name="Existing TG",
        )

        self.other_post = Post.objects.create(
            user=self.user,
            title="Other Post",
            description="Another post for testing object deletion"
        )

        self.other_tg = TagGroup.objects.create(
            user=self.user,
            name="Other TG",
        )

    def assert_object_delete(self, url, action):
        url_args = extract_url(url)
        data = {'action': action}
        parent_id = None
        other_parent_id = None
        self.assertTrue(
            Post.objects.filter(title=self.post.title, user=self.user).exists()
        )
        self.assertTrue(
            TagGroup.objects.filter(name=self.tg.name, user=self.user).exists()
        )
        before_posts_count = Post.objects.filter(user=self.user).count()
        before_tgs_count = TagGroup.objects.filter(user=self.user).count()

        if action == 'delete_post':
            parent_id = 'recent-posts'
            other_parent_id = 'recent-tgs'
            self.assertIn('post_pk', url_args)
            self.assertEqual(url_args['post_pk'], self.post.pk)
        elif action == 'delete_tg':
            parent_id = 'recent-tgs'
            other_parent_id = 'recent-posts'
            self.assertIn('tg_pk', url_args)
            self.assertEqual(url_args['tg_pk'], self.tg.pk)

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        response_url = response.request['PATH_INFO']
        self.assertIn((response_url, 302), response.redirect_chain)
        response_url_args = extract_url(response_url)

        if action == 'delete_post':
            assert_tag_not_in_list(
                response, self.post.title, parent_id, 'list-item-title'
            )
            assert_tag_in_list(
                response, self.tg.name, other_parent_id, 'list-item-title'
            )
            self.assertFalse(
                Post.objects.filter(title=self.post.title, user=self.user).exists()
            )
            self.assertNotIn('post_pk', response_url_args)

            if 'tg_pk' in url_args:
                self.assertEqual(response_url_args['tg_pk'], url_args['tg_pk'])

            self.assertEqual(
                Post.objects.filter(user=self.user).count(), before_posts_count - 1
            )
            self.assertEqual(
                TagGroup.objects.filter(user=self.user).count(), before_tgs_count
            )

        elif action == 'delete_tg':
            assert_tag_not_in_list(
                response, self.tg.name, parent_id, 'list-item-title'
            )
            assert_tag_in_list(
                response, self.post.title, other_parent_id, 'list-item-title'
            )

            self.assertFalse(
                TagGroup.objects.filter(name=self.tg.name, user=self.user).exists()
            )
            self.assertNotIn('tg_pk', response_url_args)

            if 'post_pk' in url_args:
                self.assertEqual(response_url_args['post_pk'], url_args['post_pk'])

            self.assertEqual(
                TagGroup.objects.filter(user=self.user).count(), before_tgs_count - 1
            )
            self.assertEqual(
                Post.objects.filter(user=self.user).count(), before_posts_count
            )

    def test_post_delete_on_post_page(self):
        """
        Test deleting a Post on a page with only Post chosen.
        Link: /post/<post_pk>
        """
        url = reverse('post_editor', args=[self.post.pk])
        self.assert_object_delete(url, 'delete_post')

    def test_post_delete_on_post_tg_page(self):
        """
        Test deleting a Post on a page with Post and TG chosen.
        Link: /post/<post_pk>/tg/<tg_pk>
        """
        url = reverse('post_tg_editor', args=[self.post.pk, self.tg.pk])
        self.assert_object_delete(url, 'delete_post')

    def test_tg_delete_on_tg_page(self):
        """
        Test deleting a TagGroup on a page with only TG chosen.
        Link: /tg/<tg_pk>
        """
        url = reverse('tg_editor', args=[self.tg.pk])
        self.assert_object_delete(url, 'delete_tg')

    def test_tg_delete_on_post_tg_page(self):
        """
        Test deleting a TagGroup on a page with Post and TG chosen.
        Link: /post/<post_pk>/tg/<tg_pk>
        """
        url = reverse('post_tg_editor', args=[self.post.pk, self.tg.pk])
        self.assert_object_delete(url, 'delete_tg')
