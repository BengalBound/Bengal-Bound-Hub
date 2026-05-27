"""
Migration 0011: Encrypted tokens, new SocialMediaAccount and ContentQueue fields.

Changes:
  - SocialMediaAccount.access_token: TextField → EncryptedTextField
    (column type stays TEXT — encryption is Python-level only)
  - SocialMediaAccount.last_checked_at: new DateTimeField (nullable)
  - ContentQueue.platform_post_id: new CharField (blank, default='')
  - ContentQueue.media_url: new URLField (nullable, blank)
"""
from django.db import migrations, models
import serea.encryption


class Migration(migrations.Migration):

    dependencies = [
        ('serea', '0010_neurolinkit_linkedin_campaigns'),
    ]

    operations = [
        # ── SocialMediaAccount ────────────────────────────────────────────────
        migrations.AlterField(
            model_name='socialmediaaccount',
            name='access_token',
            field=serea.encryption.EncryptedTextField(
                help_text='Primary access token. Encrypted at rest. Do not share.'
            ),
        ),
        migrations.AddField(
            model_name='socialmediaaccount',
            name='last_checked_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Timestamp of the last comment-fetch run by monitor_social_task.',
            ),
        ),
        # ── ContentQueue ──────────────────────────────────────────────────────
        migrations.AddField(
            model_name='contentqueue',
            name='platform_post_id',
            field=models.CharField(
                blank=True,
                default='',
                max_length=255,
                help_text='Post ID / URN returned by the platform API after publishing.',
            ),
        ),
        migrations.AddField(
            model_name='contentqueue',
            name='media_url',
            field=models.URLField(
                blank=True,
                max_length=500,
                null=True,
                help_text='Public URL of the image or video asset for this post.',
            ),
        ),
    ]
