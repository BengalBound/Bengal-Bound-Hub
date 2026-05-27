from django.db import models
from django.utils import timezone
from accounts.models import User


class Department(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='hr_departments')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    manager = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def employee_count(self):
        return self.employees.filter(status='active').count()


class JobPosition(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='hr_positions')
    title = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='positions')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class Employee(models.Model):
    STATUS = [('active', 'Active'), ('inactive', 'Inactive'), ('on_leave', 'On Leave'), ('terminated', 'Terminated')]
    GENDER = [('male', 'Male'), ('female', 'Female'), ('other', 'Other'), ('prefer_not', 'Prefer not to say')]
    CONTRACT = [('full_time', 'Full Time'), ('part_time', 'Part Time'), ('contractor', 'Contractor'), ('intern', 'Intern')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='hr_employees')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='hr_profiles')
    employee_id = models.CharField(max_length=20, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    gender = models.CharField(max_length=12, choices=GENDER, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    national_id = models.CharField(max_length=50, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    position = models.ForeignKey(JobPosition, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='direct_reports')
    contract_type = models.CharField(max_length=20, choices=CONTRACT, default='full_time')
    hire_date = models.DateField(default=timezone.now)
    termination_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='active')
    work_location = models.CharField(max_length=200, blank=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=5, default='USD')
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account = models.CharField(max_length=50, blank=True)
    photo = models.ImageField(upload_to='hr/photos/', null=True, blank=True)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def years_of_service(self):
        if self.hire_date:
            delta = timezone.now().date() - self.hire_date
            return round(delta.days / 365, 1)
        return 0


class LeaveType(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='hr_leave_types')
    name = models.CharField(max_length=100)
    days_allowed = models.IntegerField(default=0, help_text='Days per year, 0=unlimited')
    is_paid = models.BooleanField(default=True)
    color = models.CharField(max_length=7, default='#3b82f6')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class LeaveRequest(models.Model):
    STATUS = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='hr_leave_requests')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.SET_NULL, null=True, related_name='requests')
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.IntegerField(default=1)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_leaves')
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee} — {self.leave_type} ({self.start_date})"


class PerformanceReview(models.Model):
    RATING = [('1', 'Needs Improvement'), ('2', 'Below Expectations'), ('3', 'Meets Expectations'), ('4', 'Exceeds Expectations'), ('5', 'Outstanding')]
    STATUS = [('draft', 'Draft'), ('submitted', 'Submitted'), ('completed', 'Completed')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='hr_reviews')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='given_reviews')
    period_start = models.DateField()
    period_end = models.DateField()
    rating = models.CharField(max_length=2, choices=RATING, blank=True)
    goals_achieved = models.TextField(blank=True)
    strengths = models.TextField(blank=True)
    areas_to_improve = models.TextField(blank=True)
    overall_comments = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review: {self.employee} ({self.period_start} to {self.period_end})"
