import tempfile
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from django.contrib.auth import get_user_model
from django.test import Client
from posts.models import Post, Tag, PostTag
import time
from django.contrib.staticfiles.testing import StaticLiveServerTestCase


class TestTagReorderUI(StaticLiveServerTestCase):
    def test_post_tag_reorder_block_updates(self):
        # SETUP: create user, post, tags
        User = get_user_model()
        user = User.objects.create_user(email="test@example.com")  # allauth user
        post = Post.objects.create(user=user, title="Selenium", description="desc")
        tag1 = Tag.objects.create(name="tag_a")
        tag2 = Tag.objects.create(name="tag_b")
        PostTag.objects.create(post=post, tag=tag1, position=0)
        PostTag.objects.create(post=post, tag=tag2, position=1)

        import os
        print("Can write to /tmp:", os.access("/tmp", os.W_OK))

        # Authenticate user and get sessionid (using Django test client)
        client = Client()
        client.force_login(user)
        sessionid = client.cookies["sessionid"].value

        # Chrome options for Selenium on Alpine/CI

        with tempfile.TemporaryDirectory() as tmpdirname:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"--user-data-dir={tmpdirname}")
            chrome_options.binary_location = "/usr/bin/chromium-browser"
            # Specify exact path to chromedriver!
            driver = webdriver.Chrome(
                service=Service(executable_path="/usr/bin/chromedriver"),
                options=chrome_options
            )

        try:
            # Set sessionid cookie for authentication
            driver.get(self.live_server_url)
            # adding
            # cookies
            driver.add_cookie({
                'name': 'sessionid',
                'value': sessionid,
                'path': '/',
                'secure': False,
                'httpOnly': True,
            })

            # Go to the post editor page (edit the path as needed)
            driver.get(f"{self.live_server_url}/post/{post.id}")

            # Wait until the tags are loaded
            def tags_appeared():
                tags = driver.find_elements(By.CSS_SELECTOR, "#dnd-list-post .tag")
                return len(tags) == 2

            for _ in range(30):
                if tags_appeared():
                    break
                time.sleep(0.2)
            else:
                pytest.fail("Tags block did not appear in time")

            tags = driver.find_elements(By.CSS_SELECTOR, "#dnd-list-post .tag")

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
                new_tags = driver.find_elements(By.CSS_SELECTOR, "#dnd-list-post .tag")
                if (
                    new_tags[0].text.strip().startswith("tag_b")
                    and
                    new_tags[1].text.strip().startswith("tag_a")
                ):
                    break
                time.sleep(0.2)
            else:
                pytest.fail("Tags reorder was not reflected in the block")

            # After successful drag-and-drop and order verification:
            new_preview_div = driver.find_element(By.ID, "post-preview-tags")
            new_preview_text = new_preview_div.text.strip()
            assert new_preview_text == "#tag_b #tag_a"

        finally:
            driver.quit()
