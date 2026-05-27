from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class Course(models.Model):
    LEVEL = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('all', 'All Levels'),
    ]
    STATUS = [('draft', 'Draft'), ('published', 'Published'), ('archived', 'Archived')]
    AUDIENCE = [('students', 'Students'), ('employees', 'Employees / Staff'), ('both', 'Everyone')]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='courses')
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=30, blank=True)
    description = models.TextField(blank=True)
    instructor = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='teaching_courses')
    category = models.CharField(max_length=100, blank=True)
    level = models.CharField(max_length=15, choices=LEVEL, default='all')
    status = models.CharField(max_length=10, choices=STATUS, default='draft')
    audience = models.CharField(max_length=10, choices=AUDIENCE, default='students')
    duration_hours = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    is_self_paced = models.BooleanField(default=True)
    pass_score_pct = models.IntegerField(default=70)
    certificate_on_completion = models.BooleanField(default=False)
    thumbnail = models.ImageField(upload_to='lms/thumbnails/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def lesson_count(self):
        return Lesson.objects.filter(module__course=self).count()

    @property
    def enrolled_count(self):
        return self.enrollments.count()

    def __str__(self):
        return self.title


class CourseModule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} — {self.title}"


class Lesson(models.Model):
    CONTENT_TYPE = [
        ('text', 'Text / Article'),
        ('video', 'Video URL'),
        ('file', 'File Upload'),
        ('link', 'External Link'),
        ('quiz', 'Quiz / Assessment'),
    ]

    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE, default='text')
    content_text = models.TextField(blank=True)
    content_url = models.URLField(blank=True)
    content_file = models.FileField(upload_to='lms/files/', null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class LearnerEnrollment(models.Model):
    STATUS = [
        ('enrolled', 'Enrolled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    learner = models.ForeignKey(BusinessEmployee, on_delete=models.CASCADE, related_name='course_enrollments')
    status = models.CharField(max_length=15, choices=STATUS, default='enrolled')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress_pct = models.IntegerField(default=0)
    certificate_issued = models.BooleanField(default=False)

    class Meta:
        unique_together = ['course', 'learner']

    def __str__(self):
        return f"{self.learner.user.get_full_name()} → {self.course.title}"


class LessonProgress(models.Model):
    enrollment = models.ForeignKey(LearnerEnrollment, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['enrollment', 'lesson']
