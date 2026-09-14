from django.shortcuts import render
from django.http import HttpResponse
from .models import Post

# Create your views here.
def home(request):
    return render(request, 'blog/home.html')

def post(request):
    posts = Post.objects.all()

    return render(
        request,
        "blog/post.html",
        {
            "posts": posts
        }
    )
    
    
def post_detail(request, slug):
    post = Post.objects.get(slug=slug)

    return render(
        request,
        "blog/post_detail.html",
        {
            "post": post
        }
    )