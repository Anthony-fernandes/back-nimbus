from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("communication", "0001_initial"),
        ("knowledge", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="knowledgearticle",
            name="source_forum_topic",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="knowledge_articles",
                to="communication.forumtopic",
            ),
        ),
        migrations.AddField(
            model_name="knowledgearticle",
            name="source_doubts_question",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="knowledge_articles",
                to="communication.doubtsquestion",
            ),
        ),
    ]
