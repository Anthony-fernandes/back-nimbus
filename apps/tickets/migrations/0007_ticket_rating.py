from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0006_ticket_approval_conversion"),
    ]

    operations = [
        migrations.AddField(
            model_name="ticket",
            name="rating",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="ticket",
            name="rating_comment",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="ticket",
            name="rated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
