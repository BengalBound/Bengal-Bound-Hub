from django.db import models
from accounts.models import User


class Course(models.Model):
    LEVEL = [('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')]
    STATUS = [('draft', 'Draft'), ('published', 'Published'), ('archived', 'Archived')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='training_courses')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    description = models.TextField()
    level = models.CharField(max_length=20, choices=LEVEL, default='beginner')
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    duration_hours = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    thumbnail = models.ImageField(upload_to='training/thumbnails/', null=True, blank=True)
    category = models.CharField(max_length=100, blank=True)
    tags = models.CharField(max_length=300, blank=True)
    is_mandatory = models.BooleanField(default=False)
    target_departments = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_courses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

    def completion_rate(self):
        total = self.enrollments.count()
        if not total:
            return 0
        done = self.enrollments.filter(status='completed').count()
        return round(done / total * 100)


class CourseModule(models.Model):
    TYPE = [('video', 'Video'), ('article', 'Article'), ('quiz', 'Quiz'), ('assignment', 'Assignment'), ('document', 'Document')]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    module_type = models.CharField(max_length=20, choices=TYPE, default='article')
    content = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    document = models.FileField(upload_to='training/documents/', null=True, blank=True)
    duration_minutes = models.IntegerField(default=0)
    position = models.IntegerField(default=0)
    is_required = models.BooleanField(default=True)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.title} ({self.course.title})"


class Enrollment(models.Model):
    STATUS = [('enrolled', 'Enrolled'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('dropped', 'Dropped')]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    employee = models.ForeignKey('hr.Employee', on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS, default='enrolled')
    progress_pct = models.IntegerField(default=0)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    certificate_issued = models.BooleanField(default=False)

    class Meta:
        ordering = ['-enrolled_at']
        unique_together = [('course', 'employee')]

    def __str__(self):
        return f"{self.employee} → {self.course}"


class Quiz(models.Model):
    module = models.OneToOneField(CourseModule, on_delete=models.CASCADE, related_name='quiz')
    passing_score = models.IntegerField(default=70)
    time_limit_minutes = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quiz: {self.module.title}"


class QuizQuestion(models.Model):
    TYPE = [('mcq', 'Multiple Choice'), ('true_false', 'True/False'), ('short', 'Short Answer')]
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question = models.TextField()
    question_type = models.CharField(max_length=10, choices=TYPE, default='mcq')
    points = models.IntegerField(default=1)
    position = models.IntegerField(default=0)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return self.question[:100]


class QuizChoice(models.Model):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text
