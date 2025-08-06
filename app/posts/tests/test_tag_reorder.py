import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from django.contrib.auth import get_user_model
from django.test import Client
from posts.models import Post, Tag, TagGroup
import time
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

User = get_user_model()

POST_TAG_LIST_ID = 'dnd-list-post'
TG_TAG_LIST_ID = 'dnd-list-tg'


class TestTagReorderUI(StaticLiveServerTestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com")  # allauth user
        self.post = Post.objects.create(
            user=self.user,
            title="Selenium",
            description="desc"
        )
        self.tag1 = Tag.objects.create(name="tag_a")
        self.tag2 = Tag.objects.create(name="tag_b")
        self.post.update_tags([self.tag1.id, self.tag2.id])
        self.tg = TagGroup.objects.create(name="test_tg", user=self.user)

    def assert_tag_order(self, tag_list_id, relative_path):
        # Authenticate user and get sessionid (using Django test client)
        client = Client()
        client.force_login(self.user)
        sessionid = client.cookies["sessionid"].value

        # Chrome options for Selenium on Alpine/CI
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.binary_location = "/usr/bin/chromium"
        # Specify exact path to chromedriver!
        driver = webdriver.Chrome(
            service=Service(executable_path="/usr/bin/chromedriver"),
            options=chrome_options
        )

        try:
            # Set window size to ensure all content is visible
            driver.set_window_size(1366, 768)

            # Set sessionid cookie for authentication
            driver.get(self.live_server_url)
            # adding cookie
            driver.add_cookie({
                'name': 'sessionid',
                'value': sessionid,
                'path': '/',
                'secure': False,
                'httpOnly': True,
            })

            # Go to the page
            driver.get(f"{self.live_server_url}{relative_path}")

            # Wait until the tags are loaded
            def tags_appeared():
                tags = driver.find_elements(By.CSS_SELECTOR, f'#{tag_list_id} .tag')
                return len(tags) == 2

            for _ in range(30):
                if tags_appeared():
                    break
                time.sleep(0.2)
            else:
                pytest.fail("Tags block did not appear in time")

            tags = driver.find_elements(By.CSS_SELECTOR, f'#{tag_list_id} .tag')

            assert tags[0].text.strip().startswith("tag_a")
            assert tags[1].text.strip().startswith("tag_b")

            preview_div = driver.find_element(By.ID, "post-preview-tags")
            preview_text = preview_div.text.strip()
            assert preview_text == "#tag_a #tag_b"

            # Drag tag2 (B) above tag1 (A)
            tag_a = tags[0]
            tag_b = tags[1]

            # Use ActionChains for drag-and-drop
            # (might require tweaking offsets based on Sortable.js)
            actions = ActionChains(driver)
            actions.click_and_hold(tag_b).move_to_element(tag_a).move_by_offset(
                0, -10).release().perform()

            # Wait for AJAX/UI update to finish (time/detector may be improved)
            for _ in range(30):
                new_tags = driver.find_elements(By.CSS_SELECTOR, f'#{tag_list_id} .tag')
                if (
                    new_tags[0].text.strip().startswith("tag_b")
                    and
                    new_tags[1].text.strip().startswith("tag_a")
                ):
                    break
                time.sleep(0.2)
            else:
                pytest.fail("Tags reorder was not reflected in the block")

            # Preview block should change only on changes in Post Tags order
            new_preview_div = driver.find_element(By.ID, "post-preview-tags")
            new_preview_text = new_preview_div.text.strip()
            if tag_list_id == TG_TAG_LIST_ID:
                assert new_preview_text == "#tag_a #tag_b"
            elif tag_list_id == POST_TAG_LIST_ID:
                assert new_preview_text == "#tag_b #tag_a"

        finally:
            driver.quit()

    def test_post_tag_reorder_ui_on_post_page(self):
        self.assert_tag_order(
            POST_TAG_LIST_ID, f'/post/{self.post.id}'
        )

    def test_post_tag_reorder_ui_on_post_tg_page(self):
        self.assert_tag_order(
            POST_TAG_LIST_ID, f'/post/{self.post.id}/tg/{self.tg.id}'
        )
