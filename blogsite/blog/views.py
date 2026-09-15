from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Post

# Create your views here.
def home(request):
    latest_post = Post.objects.filter(
        status=Post.Status.PUBLISHED
    ).order_by("-created_at").first()

    return render(
        request,
        "blog/home.html",
        {"latest_post": latest_post}
    )

def post(request):
    posts = Post.objects.filter(
        status=Post.Status.PUBLISHED
    ).order_by("-created_at")

    paginator = Paginator(posts, 5)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "blog/post.html",
        {"page_obj": page_obj}
    )
    
    
def post_detail(request, slug):
    post = get_object_or_404(
        Post,
        slug=slug,
        status=Post.Status.PUBLISHED)

    return render(
        request,
        "blog/post_detail.html",
        {
            "post": post
        }
    )