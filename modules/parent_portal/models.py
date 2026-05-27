import secrets
from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class ProgressReport(models.Model):
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='progress_reports')
    student_name = models.CharField(max_length=150)
    student_ref = models.CharField(max_length=50, blank=True, verbose_name='Enrollment / Student ID')
    class_group = models.CharField(max_length=50, blank=True)
    period = models.CharField(max_length=50)
    report_date = models.DateField()
    overall_grade = models.CharField(max_length=10, blank=True)
    gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    attendance_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    teacher_comments = models.TextField(blank=True)
    generated_by = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_reports')
    is_shared = models.BooleanField(default=False)
    share_token = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-report_date']

    def generate_share_link(self):
        self.share_token = secrets.token_urlsafe(32)
        self.is_shared = True
        self.save(update_fields=['share_token', 'is_shared'])

    def __str__(self):
        return f"{self.student_name} — {self.period}"


class ReportSubjectLine(models.Model):
    report = models.ForeignKey(ProgressReport, on_delete=models.CASCADE, related_name='subject_lines')
    subject = models.CharField(max_length=100)
    score = models.CharField(max_length=20, blank=True)
    grade = models.CharField(max_length=10, blank=True)
    teacher = models.CharField(max_length=100, blank=True)
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ['subject']


class ParentMessage(models.Model):
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='parent_messages')
    from_employee = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, related_name='sent_parent_messages')
    parent_name = models.CharField(max_length=150)
    parent_email = models.EmailField(blank=True)
    student_name = models.CharField(max_length=150)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_urgent = models.BooleanField(default=False)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"To: {self.parent_name} re: {self.student_name}"


class Announcement(models.Model):
    AUDIENCE = [('all', 'All Parents'), ('class', 'Specific Class'), ('individual', 'Individual Student')]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='portal_announcements')
    title = models.CharField(max_length=200)
    body = models.TextField()
    audience = models.CharField(max_length=12, choices=AUDIENCE, default='all')
    class_group = models.CharField(max_length=50, blank=True)
    posted_by = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True)
    posted_at = models.DateTimeField(auto_now_add=True)
    is_pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_pinned', '-posted_at']
