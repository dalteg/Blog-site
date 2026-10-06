from django.test import TestCase
from django.contrib.auth import get_user_model

from .models import Post


class PostSlugIndexTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="author")

    def test_slug_requires_manual_value_and_is_indexed(self):
        field = Post._meta.get_field("slug")
        self.assertTrue(field.unique)
        self.assertTrue(field.db_index)
        self.assertTrue(field.blank is False)
        self.assertTrue(field.editable)
