from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .forms import CommentForm, PostForm
from .models import Comment, Post, Tag


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

    def test_detail_shows_comment_form_and_existing_comments(self):
        post = Post.objects.create(
            title="Post with comments",
            slug="post-with-comments",
            content="Post content",
            status=Post.Status.PUBLISHED,
            author=self.author,
        )
        comment = Comment.objects.create(
            post=post,
            author_name="Reader",
            author_email="reader@example.com",
            content="A helpful comment",
        )

        response = self.client.get(
            reverse("post-detail", kwargs={"slug": post.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["comments"]), [comment])
        self.assertIsInstance(response.context["comment_form"], CommentForm)
        self.assertContains(response, "A helpful comment")
        self.assertContains(response, "Reader")
        self.assertNotContains(response, "reader@example.com")

    def test_visitor_can_submit_comment(self):
        post = Post.objects.create(
            title="Open comments",
            slug="open-comments",
            content="Post content",
            status=Post.Status.PUBLISHED,
            author=self.author,
        )

        response = self.client.post(
            reverse("post-detail", kwargs={"slug": post.slug}),
            {
                "author_name": "Visitor",
                "author_email": "visitor@example.com",
                "content": "My comment",
            },
        )

        comment = Comment.objects.get(post=post)
        self.assertEqual(comment.author_name, "Visitor")
        self.assertEqual(comment.author_email, "visitor@example.com")
        self.assertEqual(comment.content, "My comment")
        self.assertIsNone(comment.author)
        self.assertRedirects(
            response,
            f"{reverse('post-detail', kwargs={'slug': post.slug})}#comments",
        )

    def test_invalid_comment_is_not_saved_and_form_errors_are_shown(self):
        post = Post.objects.create(
            title="Open comments",
            slug="open-comments",
            content="Post content",
            status=Post.Status.PUBLISHED,
            author=self.author,
        )

        response = self.client.post(
            reverse("post-detail", kwargs={"slug": post.slug}),
            {
                "author_name": "Visitor",
                "author_email": "not-an-email",
                "content": "My comment",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.filter(post=post).count(), 0)
        self.assertFormError(
            response.context["comment_form"],
            "author_email",
            "Enter a valid email address.",
        )

    def test_comments_cannot_be_submitted_when_disabled(self):
        post = Post.objects.create(
            title="Closed comments",
            slug="closed-comments",
            content="Post content",
            status=Post.Status.PUBLISHED,
            allow_comments=False,
            author=self.author,
        )

        response = self.client.post(
            reverse("post-detail", kwargs={"slug": post.slug}),
            {
                "author_name": "Visitor",
                "author_email": "visitor@example.com",
                "content": "My comment",
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Comment.objects.filter(post=post).count(), 0)


class PostFormViewTests(TestCase):
    def setUp(self):
        self.staff_user = get_user_model().objects.create_user(
            username="staff",
            password="password",
            is_staff=True,
        )
        self.regular_user = get_user_model().objects.create_user(
            username="reader",
            password="password",
        )

    def test_anonymous_user_is_redirected_to_admin_login(self):
        response = self.client.get(reverse("post-create"))

        self.assertRedirects(
            response,
            f"{reverse('admin:login')}?next={reverse('post-create')}",
        )

    def test_non_staff_user_cannot_create_or_edit_posts(self):
        self.client.force_login(self.regular_user)

        create_response = self.client.get(reverse("post-create"))
        post = Post.objects.create(
            title="Draft",
            slug="draft",
            content="Draft content",
            author=self.staff_user,
        )
        edit_response = self.client.get(
            reverse("post-edit", kwargs={"slug": post.slug})
        )

        self.assertEqual(create_response.status_code, 403)
        self.assertEqual(edit_response.status_code, 403)

    def test_staff_can_create_post_with_generated_unique_slug(self):
        self.client.force_login(self.staff_user)
        Post.objects.create(
            title="A New Story!",
            slug="a-new-story",
            content="Existing story",
            author=self.staff_user,
        )

        response = self.client.post(
            reverse("post-create"),
            {
                "title": "A New Story!",
                "content": "New content",
                "status": Post.Status.DRAFT,
                "allow_comments": "on",
            },
        )

        created_post = Post.objects.get(content="New content")
        self.assertEqual(created_post.slug, "a-new-story-2")
        self.assertEqual(created_post.author, self.staff_user)
        self.assertRedirects(
            response,
            reverse("post-edit", kwargs={"slug": created_post.slug}),
        )

    def test_editing_post_keeps_its_existing_slug(self):
        self.client.force_login(self.staff_user)
        post = Post.objects.create(
            title="Original title",
            slug="original-title",
            content="Original content",
            author=self.staff_user,
        )

        response = self.client.post(
            reverse("post-edit", kwargs={"slug": post.slug}),
            {
                "title": "Updated title",
                "content": "Updated content",
                "status": Post.Status.DRAFT,
                "allow_comments": "on",
            },
        )

        post.refresh_from_db()
        self.assertEqual(post.slug, "original-title")
        self.assertEqual(post.title, "Updated title")
        self.assertRedirects(
            response,
            reverse("post-edit", kwargs={"slug": post.slug}),
        )

    def test_editing_tags_adds_new_tags_and_unassigns_removed_tags(self):
        self.client.force_login(self.staff_user)
        removed_tag = Tag.objects.create(name="old tag")
        retained_tag = Tag.objects.create(name="shared tag")
        post = Post.objects.create(
            title="Tag editing",
            slug="tag-editing",
            content="Content",
            author=self.staff_user,
        )
        post.tags.add(removed_tag, retained_tag)
        another_post = Post.objects.create(
            title="Another post",
            slug="another-post",
            content="Content",
            author=self.staff_user,
        )
        another_post.tags.add(removed_tag)

        response = self.client.post(
            reverse("post-edit", kwargs={"slug": post.slug}),
            {
                "title": post.title,
                "content": post.content,
                "status": Post.Status.DRAFT,
                "allow_comments": "on",
                "tag_names": "shared tag, new tag",
            },
        )

        post.refresh_from_db()
        self.assertEqual(
            set(post.tags.values_list("name", flat=True)),
            {"shared tag", "new tag"},
        )
        self.assertTrue(Tag.objects.filter(pk=removed_tag.pk).exists())
        self.assertTrue(another_post.tags.filter(pk=removed_tag.pk).exists())
        self.assertRedirects(
            response,
            reverse("post-edit", kwargs={"slug": post.slug}),
        )

    def test_edit_form_shows_current_tags(self):
        self.client.force_login(self.staff_user)
        post = Post.objects.create(
            title="Tagged post",
            slug="tagged-post",
            content="Content",
            author=self.staff_user,
        )
        post.tags.create(name="existing tag")

        response = self.client.get(
            reverse("post-edit", kwargs={"slug": post.slug})
        )

        self.assertContains(response, 'value="existing tag"')

    def test_form_does_not_expose_slug_or_author(self):
        form = PostForm()

        self.assertNotIn("slug", form.fields)
        self.assertNotIn("author", form.fields)
        self.assertNotIn("tags", form.fields)


class CommentFormTests(TestCase):
    def test_comment_form_does_not_expose_post_or_account(self):
        form = CommentForm()

        self.assertEqual(
            set(form.fields),
            {"author_name", "author_email", "content"},
        )


class PostSlugIndexTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="author")

    def test_slug_requires_manual_value_and_is_indexed(self):
        field = Post._meta.get_field("slug")
        self.assertTrue(field.unique)
        self.assertTrue(field.db_index)
        self.assertTrue(field.blank is False)
        self.assertTrue(field.editable)
