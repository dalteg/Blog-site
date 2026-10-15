from django.views.generic import DetailView, ListView
from .models import Post


class HomeView(ListView):
    template_name = "blog/home.html"
    model = Post
    context_object_name = "posts"

    def get_queryset(self):
        return super().get_queryset().filter(
            status=Post.Status.PUBLISHED
        ).order_by("-created_at")


class PostListView(ListView):
    template_name = "blog/post.html"
    model = Post
    context_object_name = "posts"
    paginate_by = 5

    def get_queryset(self):
        return super().get_queryset().filter(
            status=Post.Status.PUBLISHED
        ).order_by("-created_at")

    def paginate_queryset(self, queryset, page_size):
        paginator = self.get_paginator(
            queryset,
            page_size,
            allow_empty_first_page=self.get_allow_empty(),
        )
        page = paginator.get_page(self.request.GET.get(self.page_kwarg))
        return paginator, page, page.object_list, page.has_other_pages()


class PostDetailView(DetailView):
    template_name = "blog/post_detail.html"
    model = Post
    context_object_name = "post"

    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)