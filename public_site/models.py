from django.db import models
from django.conf import settings

class Service(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    icon_class = models.CharField(max_length=50, help_text="Bootstrap icon class (e.g., bi-robot)", blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Product(models.Model):
    TYPE_CHOICES = (
        ('standard', 'Standard Product'),
        ('tool', 'Tool'),
        ('ai_agent', 'AI Agent'),
    )
    product_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='standard')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    tagline = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.get_product_type_display()}] {self.name}"

class BlogCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = "Blog Categories"

    def __str__(self):
        return self.name

class BlogPost(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, related_name='posts')
    content = models.TextField()
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class BlogComment(models.Model):
    post = models.ForeignKey('BlogPost', on_delete=models.CASCADE, related_name='comments')
    author_name = models.CharField(max_length=150)
    author_email = models.EmailField()
    content = models.TextField()
    is_approved = models.BooleanField(default=False)
    admin_reply = models.TextField(blank=True, help_text="Workspace Admin's reply to this comment")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author_name} on {self.post.title}"

class ContactInquiry(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Contact Inquiries"

    def __str__(self):
        return f"{self.subject} - {self.email}"

class ConsultationBooking(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    company_name = models.CharField(max_length=200, blank=True)
    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    notes = models.TextField(blank=True)
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking: {self.name} on {self.preferred_date}"

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.question

class VideoRepresentation(models.Model):
    title = models.CharField(max_length=255)
    video_url = models.URLField(help_text="Direct link to video or embedded url (Youtube/Vimeo)")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class VideoReview(models.Model):
    reviewer_name = models.CharField(max_length=150)
    company_name = models.CharField(max_length=150, blank=True)
    video_url = models.URLField(help_text="Link to review video")
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.reviewer_name}"


class HomepageContent(models.Model):
    """Singleton model to control homepage hero content"""
    hero_title1 = models.CharField(max_length=100, default="Next-Gen Workforces.")
    hero_title2 = models.CharField(max_length=100, default="Automated & Unbound.")
    hero_subtitle = models.TextField(default="BengalBound provides leading WaaS and AIaaS.")
    
    primary_button_text = models.CharField(max_length=50, default="Meet Serea")
    primary_button_url = models.CharField(max_length=200, default="#")
    
    secondary_button_text = models.CharField(max_length=50, default="View Services")
    secondary_button_url = models.CharField(max_length=200, default="/services/")

    def __str__(self):
        return "Homepage Content Settings"

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(id=self.id).delete()
        super().save(*args, **kwargs)

class CompanyDetails(models.Model):
    """Singleton model to control company contact information"""
    address = models.TextField(default="123 AI Boulevard\nTech District, Innovation City 90210")
    phone = models.CharField(max_length=50, default="+1 (555) 123-4567")
    email = models.EmailField(default="hello@bengalbound.com")
    working_hours = models.CharField(max_length=100, default="Mon - Fri, 9am - 6pm EST")
    
    class Meta:
        verbose_name_plural = "Company Details"

    def __str__(self):
        return "Company Contact Information"

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(id=self.id).delete()
        super().save(*args, **kwargs)

class TeamMember(models.Model):
    """CMS-controlled team section. Editable from Workspace Panel."""
    name = models.CharField(max_length=150)
    role = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    photo_url = models.URLField(blank=True, help_text="URL to team member photo")
    linkedin_url = models.URLField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.name} — {self.role}"

class NavbarItem(models.Model):
    """CMS-controlled navbar links. Editable from Workspace Panel."""
    LINK_TYPES = (
        ('internal', 'Internal Page'),
        ('external', 'External URL'),
        ('dropdown_parent', 'Dropdown Parent'),
    )
    label = models.CharField(max_length=100)
    url = models.CharField(max_length=255, blank=True)
    link_type = models.CharField(max_length=20, choices=LINK_TYPES, default='internal')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.label

class FooterLink(models.Model):
    """CMS-controlled footer links grouped by section. Editable from Workspace Panel."""
    SECTION_CHOICES = (
        ('company', 'Company'),
        ('services', 'Services'),
        ('resources', 'Resources'),
        ('legal', 'Legal'),
    )
    section = models.CharField(max_length=20, choices=SECTION_CHOICES, default='company')
    label = models.CharField(max_length=100)
    url = models.CharField(max_length=255)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['section', 'order']

    def __str__(self):
        return f"[{self.get_section_display()}] {self.label}"

class TrialAccount(models.Model):
    """Tracks free trial requests from the marketing site."""
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('active', 'Trial Active'),
        ('converted', 'Converted to Paid'),
        ('expired', 'Trial Expired'),
    )
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    company_name = models.CharField(max_length=200, blank=True)
    use_case = models.TextField(help_text="What will they use the platform for?")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    # Link to actual account once created
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='trial')
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trial: {self.email} ({self.get_status_display()})"

class CoreValue(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField()
    icon_class = models.CharField(max_length=50, help_text="Bootstrap icon class (e.g., bi-rocket)", blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

class PlatformFeature(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField()
    icon_class = models.CharField(max_length=50, help_text="Bootstrap icon class (e.g., bi-laptop)", blank=True)
    image = models.ImageField(upload_to='platform_features/', blank=True, null=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

class WorkProcessStep(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField()
    step_number = models.IntegerField(default=1)
    icon_class = models.CharField(max_length=50, help_text="Bootstrap icon class", blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['step_number']

    def __str__(self):
        return f"Step {self.step_number}: {self.title}"

class Testimonial(models.Model):
    client_name = models.CharField(max_length=150)
    role = models.CharField(max_length=100, blank=True)
    company = models.CharField(max_length=150, blank=True)
    content = models.TextField()
    rating = models.IntegerField(default=5, help_text="Rating out of 5")
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Testimonial from {self.client_name}"


class DocumentationCategory(models.Model):
    """Filter tabs displayed above the documentation cards section."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name_plural = "Documentation Categories"

    def __str__(self):
        return self.name


class Documentation(models.Model):
    """Cards shown in the public-facing Documentation section."""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    excerpt = models.TextField(help_text="Short summary shown on the card.", blank=True)
    thumbnail = models.ImageField(
        upload_to='docs/thumbnails/',
        blank=True, null=True,
        help_text="Card preview image (recommended: 600x400px)"
    )
    author_name = models.CharField(max_length=150, default="BengalBound Team")
    author_avatar = models.ImageField(upload_to='docs/avatars/', blank=True, null=True)
    category = models.ForeignKey(
        DocumentationCategory,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='docs'
    )
    view_count = models.PositiveIntegerField(default=0)
    external_url = models.URLField(
        blank=True,
        help_text="If set, the card links here instead of an internal page."
    )
    youtube_url = models.URLField(
        blank=True,
        help_text="YouTube video URL (e.g. https://youtube.com/watch?v=...). Adds a play button to the card."
    )
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title


class Partner(models.Model):
    """Partner / client logos shown in the homepage marquee."""
    name    = models.CharField(max_length=120)
    logo    = models.ImageField(
        upload_to='partners/',
        help_text="Upload the partner logo (SVG, PNG, or WebP recommended, transparent background)."
    )
    website = models.URLField(blank=True, help_text="Partner website URL (optional).")
    order   = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name
