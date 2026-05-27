from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class Student(models.Model):
    GENDER = [('M', 'Male'), ('F', 'Female'), ('O', 'Other / Prefer not to say')]
    STATUS = [
        ('active', 'Active'),
        ('graduated', 'Graduated'),
        ('suspended', 'Suspended'),
        ('withdrawn', 'Withdrawn'),
        ('transferred', 'Transferred'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='students')
    enrollment_number = models.CharField(max_length=50)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER, blank=True)
    photo = models.ImageField(upload_to='sis/photos/', null=True, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    class_group = models.CharField(max_length=50, blank=True, verbose_name='Class / Grade')
    section = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=15, choices=STATUS, default='active')
    enrolled_date = models.DateField(null=True, blank=True)
    graduation_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        unique_together = ['business', 'enrollment_number']

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return f"{self.full_name} ({self.enrollment_number})"


class ParentGuardian(models.Model):
    RELATIONSHIP = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Legal Guardian'),
        ('sibling', 'Sibling'),
        ('other', 'Other'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='parents')
    name = models.CharField(max_length=150)
    relationship = models.CharField(max_length=10, choices=RELATIONSHIP, default='guardian')
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.get_relationship_display()})"


class SubjectGrade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    subject = models.CharField(max_length=100)
    period = models.CharField(max_length=50, verbose_name='Term / Semester / Period')
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    grade_letter = models.CharField(max_length=5, blank=True)
    recorded_by = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-recorded_at']

    @property
    def percentage(self):
        if self.score is not None and self.max_score:
            return round((self.score / self.max_score) * 100, 1)
        return None


class StudentAttendance(models.Model):
    STATUS = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
        ('half_day', 'Half Day'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS, default='present')
    subject = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['student', 'date', 'subject']
