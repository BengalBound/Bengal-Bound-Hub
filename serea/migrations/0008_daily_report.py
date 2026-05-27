from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('serea', '0007_serea_tasks'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_date', models.DateField()),
                ('summary', models.TextField(blank=True, help_text="Serea's narrative end-of-day summary")),
                ('status', models.CharField(
                    choices=[
                        ('pending',    'Pending Review'),
                        ('reviewed',   'Reviewed'),
                        ('approved',   'Approved'),
                        ('has_issues', 'Has Issues — Serea is fixing'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('client_feedback', models.TextField(blank=True, default='')),
                ('feedback_sent_at', models.DateTimeField(blank=True, null=True)),
                ('agent', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='daily_reports',
                    to='serea.sereaagent',
                )),
                ('reviewed_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='reviewed_reports',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Daily Report',
                'verbose_name_plural': 'Daily Reports',
                'ordering': ['-report_date'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='dailyreport',
            unique_together={('agent', 'report_date')},
        ),
        migrations.CreateModel(
            name='DailyReportItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_type', models.CharField(
                    choices=[
                        ('task',       'Task'),
                        ('post',       'Post Scheduled/Published'),
                        ('moderation', 'Moderation Action'),
                        ('dm',         'DM / Comment Reply'),
                        ('general',    'General Update'),
                    ],
                    default='general',
                    max_length=20,
                )),
                ('title', models.CharField(max_length=255)),
                ('detail', models.TextField(blank=True, default='')),
                ('outcome', models.CharField(
                    choices=[
                        ('completed',        'Completed'),
                        ('in_progress',      'In Progress'),
                        ('waiting_approval', 'Waiting for Approval'),
                        ('failed',           'Failed'),
                        ('skipped',          'Skipped'),
                    ],
                    default='completed',
                    max_length=20,
                )),
                ('is_flagged', models.BooleanField(default=False)),
                ('flag_reason', models.TextField(blank=True, default='')),
                ('client_action', models.CharField(
                    choices=[
                        ('none',           'No Action'),
                        ('reassign',       'Reassign to Serea'),
                        ('fixed_manually', 'Fixed Manually'),
                    ],
                    default='none',
                    max_length=20,
                )),
                ('order', models.PositiveIntegerField(default=0)),
                ('linked_task', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='report_items',
                    to='serea.sereatask',
                )),
                ('report', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='items',
                    to='serea.dailyreport',
                )),
            ],
            options={
                'verbose_name': 'Daily Report Item',
                'verbose_name_plural': 'Daily Report Items',
                'ordering': ['order', 'id'],
            },
        ),
    ]
