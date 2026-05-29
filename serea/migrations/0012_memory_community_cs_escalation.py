"""
Migration 0012: Serea full-scope employee models.

New models:
  - SereaMemory          — Serea's persistent long-term memory
  - CommunityMemberProfile — Tracks individual platform users
  - CustomerServiceThread  — Tracks ongoing customer service conversations
  - EscalationRecord       — Logs escalations to internal teams
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serea', '0011_encryption_platform_post_fields'),
    ]

    operations = [
        # ── SereaMemory ───────────────────────────────────────────────────────
        migrations.CreateModel(
            name='SereaMemory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('memory_type', models.CharField(
                    choices=[
                        ('user', 'Platform User Note'),
                        ('brand', 'Brand Voice / Policy Note'),
                        ('community', 'Community Situation'),
                        ('customer', 'Customer Issue Note'),
                        ('offender', 'Repeat Offender Record'),
                        ('general', 'General Note'),
                    ],
                    default='general',
                    max_length=20,
                )),
                ('subject', models.CharField(
                    max_length=255,
                    help_text="Who or what this memory is about.",
                )),
                ('platform', models.CharField(blank=True, default='', max_length=20)),
                ('content', models.TextField()),
                ('importance', models.CharField(
                    choices=[
                        ('low', 'Low'),
                        ('medium', 'Medium'),
                        ('high', 'High'),
                        ('critical', 'Critical'),
                    ],
                    default='medium',
                    max_length=10,
                )),
                ('is_active', models.BooleanField(default=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('agent', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='memories',
                    to='serea.sereaagent',
                )),
            ],
            options={
                'verbose_name': 'Serea Memory',
                'verbose_name_plural': 'Serea Memories',
                'ordering': ['-importance', '-created_at'],
            },
        ),

        # ── CommunityMemberProfile ────────────────────────────────────────────
        migrations.CreateModel(
            name='CommunityMemberProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(max_length=20)),
                ('platform_user_id', models.CharField(max_length=255)),
                ('username', models.CharField(max_length=255)),
                ('display_name', models.CharField(blank=True, default='', max_length=255)),
                ('welcomed_at', models.DateTimeField(blank=True, null=True)),
                ('engagement_score', models.FloatField(default=0.5)),
                ('violation_count', models.IntegerField(default=0)),
                ('is_flagged', models.BooleanField(default=False)),
                ('is_blocked', models.BooleanField(default=False)),
                ('flag_reason', models.TextField(blank=True, default='')),
                ('notes', models.TextField(blank=True, default='')),
                ('first_seen_at', models.DateTimeField(auto_now_add=True)),
                ('last_seen_at', models.DateTimeField(auto_now=True)),
                ('agent', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='community_members',
                    to='serea.sereaagent',
                )),
            ],
            options={
                'verbose_name': 'Community Member',
                'verbose_name_plural': 'Community Members',
                'ordering': ['-last_seen_at'],
                'unique_together': {('agent', 'platform', 'platform_user_id')},
            },
        ),

        # ── CustomerServiceThread ─────────────────────────────────────────────
        migrations.CreateModel(
            name='CustomerServiceThread',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(max_length=20)),
                ('platform_thread_id', models.CharField(blank=True, default='', max_length=255)),
                ('customer_name', models.CharField(max_length=255)),
                ('customer_platform_id', models.CharField(blank=True, default='', max_length=255)),
                ('subject', models.CharField(max_length=255)),
                ('status', models.CharField(
                    choices=[
                        ('open', 'Open'),
                        ('in_progress', 'In Progress'),
                        ('waiting_customer', 'Waiting on Customer'),
                        ('escalated', 'Escalated'),
                        ('resolved', 'Resolved'),
                        ('closed', 'Closed'),
                    ],
                    default='open',
                    max_length=20,
                )),
                ('priority', models.CharField(
                    choices=[
                        ('low', 'Low'),
                        ('normal', 'Normal'),
                        ('high', 'High'),
                        ('urgent', 'Urgent'),
                    ],
                    default='normal',
                    max_length=10,
                )),
                ('serea_notes', models.TextField(blank=True, default='')),
                ('escalated_to', models.CharField(blank=True, default='', max_length=255)),
                ('resolution', models.TextField(blank=True, default='')),
                ('opened_at', models.DateTimeField(auto_now_add=True)),
                ('last_activity_at', models.DateTimeField(auto_now=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('agent', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='cs_threads',
                    to='serea.sereaagent',
                )),
            ],
            options={
                'verbose_name': 'CS Thread',
                'verbose_name_plural': 'CS Threads',
                'ordering': ['-opened_at'],
            },
        ),

        # ── EscalationRecord ──────────────────────────────────────────────────
        migrations.CreateModel(
            name='EscalationRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('escalation_type', models.CharField(
                    choices=[
                        ('pr_crisis', 'PR Crisis'),
                        ('legal', 'Legal / Compliance'),
                        ('technical', 'Technical Problem'),
                        ('harassment', 'Serious Harassment / Abuse'),
                        ('spam_attack', 'Coordinated Spam Attack'),
                        ('media', 'Media / Press Enquiry'),
                        ('regulator', 'Regulator / Government Contact'),
                        ('other', 'Other'),
                    ],
                    default='other',
                    max_length=20,
                )),
                ('description', models.TextField()),
                ('platform', models.CharField(blank=True, default='', max_length=20)),
                ('severity', models.CharField(
                    choices=[
                        ('low', 'Low'),
                        ('medium', 'Medium'),
                        ('high', 'High'),
                        ('critical', 'Critical — Act Now'),
                    ],
                    default='medium',
                    max_length=10,
                )),
                ('status', models.CharField(
                    choices=[
                        ('open', 'Open'),
                        ('in_progress', 'In Progress'),
                        ('resolved', 'Resolved'),
                    ],
                    default='open',
                    max_length=20,
                )),
                ('escalated_to', models.CharField(blank=True, default='', max_length=255)),
                ('resolution', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('agent', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='escalations',
                    to='serea.sereaagent',
                )),
            ],
            options={
                'verbose_name': 'Escalation Record',
                'verbose_name_plural': 'Escalation Records',
                'ordering': ['-created_at'],
            },
        ),
    ]
