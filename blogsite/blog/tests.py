from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Post


class HomeViewTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="author")

    def test_home_lists_only_published_posts(self):
        published_post = Post.objects.create(
            title="Published post",
            slug="published-post",
            content="Published content",
            status=Post.Status.PUBLISHED,
            author=self.author,
        )
        Post.objects.create(
            title="Draft post",
            slug="draft-post",
            content="Draft content",
            status=Post.Status.DRAFT,
            author=self.author,
        )

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["posts"]), [published_post])
        self.assertContains(response, "Published post")
        self.assertNotContains(response, "Draft post")


class PostListViewTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="author")

    def test_post_list_is_paginated_and_excludes_drafts(self):
        posts = [
            Post.objects.create(
                title=f"Published post {index}",
                slug=f"published-post-{index}",
                content="Published content",
                status=Post.Status.PUBLISHED,
                author=self.author,
            )
            for index in range(6)
        ]
        Post.objects.create(
            title="Draft post",
            slug="draft-post",
            content="Draft content",
            status=Post.Status.DRAFT,
            author=self.author,
        )

        response = self.client.get(reverse("post"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["page_obj"]), list(reversed(posts[1:])))
        self.assertEqual(response.context["page_obj"].paginator.num_pages, 2)
        self.assertNotContains(response, "Draft post")

    def test_invalid_page_numbers_keep_existing_fallback_behavior(self):
        for index in range(6):
            Post.objects.create(
                title=f"Published post {index}",
                slug=f"published-post-{index}",
                content="Published content",
                status=Post.Status.PUBLISHED,
                author=self.author,
            )

        response = self.client.get(reverse("post"), {"page": "invalid"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 1)

        response = self.client.get(reverse("post"), {"page": "99"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 2)


class PostDetailViewTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="author")

    def test_published_post_is_displayed(self):
        post = Post.objects.create(
            title="Published post",
            slug="published-post",
            content="Published content",
            status=Post.Status.PUBLISHED,
            author=self.author,
        )

        response = self.client.get(
            reverse("post-detail", kwargs={"slug": post.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["post"], post)
        self.assertContains(response, "Published post")

    def test_draft_post_returns_not_found(self):
        post = Post.objects.create(
            title="Draft post",
            slug="draft-post",
            content="Draft content",
            status=Post.Status.DRAFT,
            author=self.author,
        )

        response = self.client.get(
            reverse("post-detail", kwargs={"slug": post.slug})
        )

        self.assertEqual(response.status_code, 404)


class PostSlugIndexTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="author")

    def test_slug_requires_manual_value_and_is_indexed(self):
        field = Post._meta.get_field("slug")
        self.assertTrue(field.unique)
        self.assertTrue(field.db_index)
        self.assertTrue(field.blank is False)
        self.assertTrue(field.editable)
