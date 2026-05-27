from django.contrib import admin
from .models import (
    Service, Product, BlogCategory, BlogPost, BlogComment,
    ContactInquiry, ConsultationBooking, FAQ,
    VideoRepresentation, VideoReview, Partner, HomepageContent,
    TeamMember, NavbarItem, FooterLink, TrialAccount, CompanyDetails
)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ('is_active',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_type', 'price', 'is_active', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('product_type', 'is_active',)

@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'is_published', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ('is_published', 'category')
    search_fields = ('title', 'content')

@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'post', 'is_approved', 'created_at')
    list_filter = ('is_approved',)
    search_fields = ('author_name', 'author_email', 'content', 'admin_reply')

@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_resolved', 'created_at')
    list_filter = ('is_resolved',)
    search_fields = ('name', 'email', 'subject')

@admin.register(ConsultationBooking)
class ConsultationBookingAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'preferred_date', 'preferred_time', 'is_confirmed', 'created_at')
    list_filter = ('is_confirmed', 'preferred_date')
    search_fields = ('name', 'email', 'company_name')

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('question', 'answer')
    ordering = ('order',)

@admin.register(VideoRepresentation)
class VideoRepresentationAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title',)

@admin.register(VideoReview)
class VideoReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer_name', 'company_name', 'is_featured', 'created_at')
    list_filter = ('is_featured',)
    search_fields = ('reviewer_name', 'company_name')

@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    search_fields = ('name',)
    ordering = ('order',)

@admin.register(HomepageContent)
class HomepageContentAdmin(admin.ModelAdmin):
    list_display = ('__str__',)

    def has_add_permission(self, request):
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'role')

@admin.register(NavbarItem)
class NavbarItemAdmin(admin.ModelAdmin):
    list_display = ('label', 'url', 'link_type', 'parent', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('link_type',)

@admin.register(FooterLink)
class FooterLinkAdmin(admin.ModelAdmin):
    list_display = ('label', 'section', 'url', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('section',)

@admin.register(TrialAccount)
class TrialAccountAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'company_name', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('email', 'name', 'company_name')
    readonly_fields = ('created_at',)

@admin.register(CompanyDetails)
class CompanyDetailsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'email', 'phone')

    def has_add_permission(self, request):
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)
