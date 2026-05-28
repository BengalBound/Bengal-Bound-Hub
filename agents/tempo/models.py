from django.db import models


class Event(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="event_set")
    name = models.CharField(max_length=500)
    event_type = models.CharField(
        max_length=15,
        choices=[
            ("conference", "Conference"),
            ("workshop", "Workshop"),
            ("product_launch", "Product Launch"),
            ("team_building", "Team Building"),
            ("webinar", "Webinar"),
            ("gala", "Gala"),
        ],
    )
    date = models.DateTimeField()
    location = models.CharField(max_length=500)
    expected_headcount = models.IntegerField()
    total_budget = models.DecimalField(max_digits=12, decimal_places=2)
    spent_so_far = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=10,
        choices=[
            ("planning", "Planning"),
            ("confirmed", "Confirmed"),
            ("live", "Live"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        default="planning",
    )
    ai_plan = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return self.name


class Attendee(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="attendee_set")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="attendees")
    name = models.CharField(max_length=300)
    email = models.EmailField()
    company = models.CharField(max_length=300, blank=True)
    rsvp_status = models.CharField(
        max_length=10,
        choices=[
            ("pending", "Pending"),
            ("confirmed", "Confirmed"),
            ("declined", "Declined"),
            ("waitlist", "Waitlist"),
        ],
        default="pending",
    )
    invitation_sent = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)
    attended = models.BooleanField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} @ {self.event.name}"
