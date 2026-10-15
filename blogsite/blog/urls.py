from django.urls import path
from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("post/", views.PostListView.as_view(), name="post"),
    path("post/create/", views.PostCreateView.as_view(), name="post-create"),
    path(
        "post/<slug:slug>/edit/",
        views.PostUpdateView.as_view(),
        name="post-edit",
    ),
    path("post/<slug:slug>/", views.PostDetailView.as_view(), name="post-detail"),
]