from django.db import models


class ProcessMap(models.Model):
    STATUS = [
        ('draft', 'Draft'), ('review', 'Under Review'),
        ('approved', 'Approved'), ('archived', 'Archived'),
    ]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='process_maps')
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    version = models.CharField(max_length=20, default='1.0')
    status = models.CharField(max_length=10, choices=STATUS, default='draft')
    owner = models.ForeignKey('bredbound.BusinessEmployee', on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_processes')
    tags = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} v{self.version}"


class ProcessStep(models.Model):
    STEP_TYPES = [
        ('start', 'Start Event'), ('end', 'End Event'),
        ('task', 'Task / Activity'), ('decision', 'Decision / Gateway'),
        ('subprocess', 'Sub-process'), ('delay', 'Delay / Wait'),
        ('approval', 'Approval Gate'), ('notification', 'Notification'),
        ('system', 'System / Automated Step'),
    ]
    process_map = models.ForeignKey(ProcessMap, on_delete=models.CASCADE, related_name='steps')
    name = models.CharField(max_length=150)
    step_type = models.CharField(max_length=15, choices=STEP_TYPES, default='task')
    description = models.TextField(blank=True)
    responsible_role = models.CharField(max_length=100, blank=True)
    responsible_employee = models.ForeignKey(
        'bredbound.BusinessEmployee', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='process_steps',
    )
    duration_estimate = models.CharField(max_length=50, blank=True)
    inputs = models.TextField(blank=True)
    outputs = models.TextField(blank=True)
    tools_used = models.CharField(max_length=200, blank=True)
    sla = models.CharField(max_length=50, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.process_map.name} — Step {self.order}: {self.name}"


class ProcessFlow(models.Model):
    FLOW_TYPES = [
        ('sequence', 'Sequence Flow'),
        ('yes', 'Yes Branch'),
        ('no', 'No Branch'),
        ('exception', 'Exception Path'),
    ]
    process_map = models.ForeignKey(ProcessMap, on_delete=models.CASCADE, related_name='flows')
    from_step = models.ForeignKey(ProcessStep, on_delete=models.CASCADE, related_name='outgoing_flows')
    to_step = models.ForeignKey(ProcessStep, on_delete=models.CASCADE, related_name='incoming_flows')
    flow_type = models.CharField(max_length=10, choices=FLOW_TYPES, default='sequence')
    label = models.CharField(max_length=80, blank=True)

    def __str__(self):
        return f"{self.from_step.name} → {self.to_step.name}"


class ProcessDocument(models.Model):
    process_map = models.ForeignKey(ProcessMap, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=150)
    file = models.FileField(upload_to='process_maps/docs/', null=True, blank=True)
    url = models.URLField(blank=True)
    description = models.CharField(max_length=200, blank=True)
    uploaded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.process_map.name} — {self.title}"


class SimulationRun(models.Model):
    process_map = models.ForeignKey(ProcessMap, on_delete=models.CASCADE, related_name='simulations')
    label = models.CharField(max_length=100)
    assumptions = models.TextField(blank=True)
    results_summary = models.TextField(blank=True)
    bottleneck_step = models.ForeignKey(ProcessStep, on_delete=models.SET_NULL, null=True, blank=True)
    throughput_per_day = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    avg_cycle_time = models.CharField(max_length=50, blank=True)
    run_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    run_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-run_at']

    def __str__(self):
        return f"{self.process_map} — Simulation: {self.label}"
