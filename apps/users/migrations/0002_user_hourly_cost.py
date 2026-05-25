# Generated manually for integration hardening.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="hourly_cost",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
