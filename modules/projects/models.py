from django.db import models
from django.utils import timezone
from accounts.models import User


class Project(models.Model):
    STATUS = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    PRIORITY = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='proj_projects')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='planning')
    priority = models.CharField(max_length=20, choices=PRIORITY, default='medium')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    client_name = models.CharField(max_length=200, blank=True)
    client_email = models.EmailField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def progress_pct(self):
        total = self.tasks.count()
        if not total:
            return 0
        done = self.tasks.filter(status='done').count()
        return int((done / total) * 100)

    @property
    def overdue_task_count(self):
        today = timezone.now().date()
        return self.tasks.filter(due_date__lt=today).exclude(status='done').count()

    @property
    def total_hours_logged(self):
        from django.db.models import Sum
        result = TimeEntry.objects.filter(task__project=self).aggregate(s=Sum('hours'))['s']
        return result or 0


class Milestone(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"{self.project.name} — {self.title}"

    @property
    def is_overdue(self):
        return not self.is_completed and self.due_date < timezone.now().date()


class Task(models.Model):
    STATUS = [('todo', 'To Do'), ('in_progress', 'In Progress'), ('review', 'Review'), ('done', 'Done')]
    PRIORITY = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    milestone = models.ForeignKey(Milestone, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='todo')
    priority = models.CharField(max_length=20, choices=PRIORITY, default='medium')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='proj_assigned_tasks')
    due_date = models.DateField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_proj_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', 'due_date']

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        return self.due_date and self.due_date < timezone.now().date() and self.status != 'done'

    @property
    def hours_logged(self):
        from django.db.models import Sum
        return self.time_entries.aggregate(s=Sum('hours'))['s'] or 0


class TimeEntry(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='time_entries')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proj_time_entries')
    description = models.CharField(max_length=300, blank=True)
    hours = models.DecimalField(max_digits=5, decimal_places=1)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.task.title} — {self.hours}h on {self.date}"


class ProjectComment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proj_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user} on {self.project.name}"
