from django.test import TestCase
from .models import Service, Product, BlogCategory, BlogPost, BlogComment, ContactInquiry, ConsultationBooking, FAQ, VideoRepresentation, VideoReview, HomepageContent, CompanyDetails, TeamMember, NavbarItem, FooterLink, TrialAccount, CoreValue, PlatformFeature, WorkProcessStep, Testimonial, DocumentationCategory, Documentation, Partner

class ServiceModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Service, "objects"))

class ProductModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Product, "objects"))

class BlogCategoryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(BlogCategory, "objects"))

class BlogPostModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(BlogPost, "objects"))

class BlogCommentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(BlogComment, "objects"))

class ContactInquiryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ContactInquiry, "objects"))

class ConsultationBookingModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ConsultationBooking, "objects"))

class FAQModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(FAQ, "objects"))

class VideoRepresentationModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(VideoRepresentation, "objects"))

class VideoReviewModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(VideoReview, "objects"))

class HomepageContentModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(HomepageContent, "objects"))

class CompanyDetailsModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CompanyDetails, "objects"))

class TeamMemberModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(TeamMember, "objects"))

class NavbarItemModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(NavbarItem, "objects"))

class FooterLinkModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(FooterLink, "objects"))

class TrialAccountModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(TrialAccount, "objects"))

class CoreValueModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(CoreValue, "objects"))

class PlatformFeatureModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(PlatformFeature, "objects"))

class WorkProcessStepModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(WorkProcessStep, "objects"))

class TestimonialModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Testimonial, "objects"))

class DocumentationCategoryModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DocumentationCategory, "objects"))

class DocumentationModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Documentation, "objects"))

class PartnerModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Partner, "objects"))

