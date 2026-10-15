from django.http import Http404, HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView

from .forms import CommentForm, PostForm
from .models import Post


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = "admin:login"

    def test_func(self):
        return self.request.user.is_staff


class PostFormSuccessUrlMixin:
    def get_success_url(self):
        if self.object.status == Post.Status.PUBLISHED:
            return reverse("post-detail", kwargs={"slug": self.object.slug})
        return reverse("post-edit", kwargs={"slug": self.object.slug})


class PostCreateView(
    StaffRequiredMixin,
    PostFormSuccessUrlMixin,
    CreateView,
):
    model = Post
    form_class = PostForm
    template_name = "blog/post_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(
    StaffRequiredMixin,
    PostFormSuccessUrlMixin,
    UpdateView,
):
    model = Post
    form_class = PostForm
    template_name = "blog/post_form.html"


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comments"] = self.object.comments.order_by("created_at")
        context.setdefault("comment_form", CommentForm())
        return context

    def post(self, request, slug):
        self.object = get_object_or_404(
            self.get_queryset(),
            **{self.slug_field: slug},
        )
        if not self.object.allow_comments:
            raise Http404

        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = self.object
            comment.save()
            return HttpResponseRedirect(
                f"{reverse('post-detail', kwargs={'slug': self.object.slug})}"
                "#comments"
            )

        return self.render_to_response(
            self.get_context_data(comment_form=form)
        )