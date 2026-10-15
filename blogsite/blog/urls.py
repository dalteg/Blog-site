from django.urls import path
from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("post/", views.PostListView.as_view(), name="post"),
    path("post/<slug:slug>/", views.PostDetailView.as_view(), name="post-detail"),
]