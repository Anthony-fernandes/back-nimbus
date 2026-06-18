from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0006_org_structure'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='mfa_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='mfa_secret',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
    ]
