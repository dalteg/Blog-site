from django import forms
from django.utils.text import slugify
from django.core.exceptions import ValidationError

from .models import Comment, Post, Tag


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("author_name", "author_email", "content")
        labels = {
            "author_name": "Your name",
            "author_email": "Email address (not shown publicly)",
        }
        widgets = {
            "content": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class PostForm(forms.ModelForm):
    tag_names = forms.CharField(
        label="Tags",
        required=False,
        max_length=1000,
        help_text=(
            "Separate tags with commas. Add a new name to create a tag, "
            "or remove a name to unassign it from this post. Existing tags "
            "are not deleted."
        ),
        widget=forms.TextInput(
            attrs={"placeholder": "django, python, web development"}
        ),
    )

    class Meta:
        model = Post
        fields = (
            "title",
            "featured_image",
            "content",
            "status",
            "co_authors",
            "tag_names",
            "allow_comments",
            "featured",
        )
        widgets = {
            "content": forms.Textarea(attrs={"rows": 16}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and not self.is_bound:
            self.initial["tag_names"] = ", ".join(
                self.instance.tags.order_by("name").values_list(
                    "name",
                    flat=True,
                )
            )

        for field in self.fields.values():
            widget_class = (
                "form-check-input"
                if isinstance(field.widget, forms.CheckboxInput)
                else "form-control"
            )
            field.widget.attrs["class"] = widget_class

    def clean_tag_names(self):
        names = self.cleaned_data["tag_names"]
        unique_names = {}

        for raw_name in names.split(","):
            name = raw_name.strip()
            if not name:
                continue
            if len(name) > Tag._meta.get_field("name").max_length:
                raise ValidationError(
                    "Each tag must be %(limit)s characters or fewer.",
                    params={"limit": Tag._meta.get_field("name").max_length},
                )
            unique_names.setdefault(name.casefold(), name)

        return list(unique_names.values())

    def save(self, commit=True):
        post = super().save(commit=False)
        if not post.pk:
            base_slug = slugify(post.title)[:50].rstrip("-") or "post"
            post.slug = base_slug
            suffix = 2
            while Post.objects.filter(slug=post.slug).exists():
                suffix_text = f"-{suffix}"
                post.slug = (
                    f"{base_slug[:50 - len(suffix_text)].rstrip('-')}"
                    f"{suffix_text}"
                )
                suffix += 1

        if commit:
            post.save()
            self.save_m2m()
        return post

    def _save_m2m(self):
        super()._save_m2m()
        tags = [
                Tag.objects.get_or_create(
                    name__iexact=name,
                    defaults={"name": name},
                )[0]
                for name in self.cleaned_data["tag_names"]
        ]
        self.instance.tags.set(tags)
