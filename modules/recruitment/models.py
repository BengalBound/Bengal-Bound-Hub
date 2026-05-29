from django.db import models
from accounts.models import User


class JobPosting(models.Model):
    STATUS = [('draft', 'Draft'), ('open', 'Open'), ('closed', 'Closed'), ('cancelled', 'Cancelled')]
    TYPE = [('full_time', 'Full Time'), ('part_time', 'Part Time'), ('contract', 'Contract'), ('internship', 'Internship'), ('remote', 'Remote')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='rec_job_postings')
    title = models.CharField(max_length=200)
    department = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=200, blank=True)
    job_type = models.CharField(max_length=20, choices=TYPE, default='full_time')
    description = models.TextField()
    requirements = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    benefits = models.TextField(blank=True)
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=5, default='USD')
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    deadline = models.DateField(null=True, blank=True)
    hiring_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_postings')
    openings = models.IntegerField(default=1)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_postings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.business.name})"

    def application_count(self):
        return self.applications.count()


class Applicant(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='rec_applicants')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    linkedin = models.URLField(blank=True)
    portfolio = models.URLField(blank=True)
    resume = models.FileField(upload_to='recruitment/resumes/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Application(models.Model):
    STAGE = [
        ('applied', 'Applied'),
        ('screening', 'Screening'),
        ('interview', 'Interview'),
        ('assessment', 'Assessment'),
        ('offer', 'Offer'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]

    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='applications')
    stage = models.CharField(max_length=20, choices=STAGE, default='applied')
    cover_letter = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    rating = models.IntegerField(null=True, blank=True, help_text='1-5 stars')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_applications')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_at']
        unique_together = [('job', 'applicant')]

    def __str__(self):
        return f"{self.applicant} → {self.job.title}"


class Interview(models.Model):
    TYPE = [('phone', 'Phone Screen'), ('video', 'Video Call'), ('onsite', 'On-Site'), ('technical', 'Technical'), ('panel', 'Panel')]
    STATUS = [('scheduled', 'Scheduled'), ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('no_show', 'No Show')]

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
    interview_type = models.CharField(max_length=20, choices=TYPE, default='video')
    scheduled_at = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    location = models.CharField(max_length=200, blank=True, help_text='Room, link, or address')
    interviewers = models.ManyToManyField(User, blank=True, related_name='interviews')
    status = models.CharField(max_length=20, choices=STATUS, default='scheduled')
    feedback = models.TextField(blank=True)
    rating = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scheduled_at']

    def __str__(self):
        return f"Interview: {self.application.applicant} @ {self.scheduled_at}"
