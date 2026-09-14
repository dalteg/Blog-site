from django.contrib import admin

# Register your models here.
from .models import Tag, Post, Comment

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    filter_horizontal = ("co_authors", "tags")

admin.site.register(Tag)
admin.site.register(Comment)