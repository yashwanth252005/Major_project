# Generated for persisted XAI consistency metrics.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0002_chatsession_chatmessage"),
    ]

    operations = [
        migrations.AddField(
            model_name="scan",
            name="xai_consistency",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
