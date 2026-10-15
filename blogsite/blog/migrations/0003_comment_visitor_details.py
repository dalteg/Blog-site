from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def copy_comment_author_details(apps, schema_editor):
    Comment = apps.get_model("blog", "Comment")
    database = schema_editor.connection.alias

    for comment in Comment.objects.using(database).select_related("author").iterator():
        author = comment.author
        comment.author_name = str(author)[:150]
        comment.author_email = getattr(author, "email", "") or ""
        comment.save(
            using=database,
            update_fields=("author_name", "author_email"),
        )


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0002_alter_post_slug"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="comment",
            name="author_name",
            field=models.CharField(max_length=150, null=True),
        ),
        migrations.AddField(
            model_name="comment",
            name="author_email",
            field=models.EmailField(max_length=254, null=True),
        ),
        migrations.RunPython(copy_comment_author_details, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="comment",
            name="author_name",
            field=models.CharField(max_length=150),
        ),
        migrations.AlterField(
            model_name="comment",
            name="author_email",
            field=models.EmailField(max_length=254),
        ),
        migrations.AlterField(
            model_name="comment",
            name="author",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="comments",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
