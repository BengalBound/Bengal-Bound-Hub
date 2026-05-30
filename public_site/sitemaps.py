from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.conf import settings
from .models import BlogPost

_DOMAIN = getattr(settings, 'SITE_DOMAIN', 'bengalbound.com')


class StaticPageSitemap(Sitemap):
    changefreq = 'weekly'
    protocol = 'https'
    i18n = False

    def items(self):
        return [
            'public_site:home',
            'public_site:about',
            'public_site:services',
            'public_site:pricing',
            'public_site:contact',
            'public_site:consult',
            'public_site:ai_job_portal',
            'public_site:why_us',
            'public_site:docs_list',
            'public_site:blog_list',
            'public_site:privacy',
            'public_site:terms',
        ]

    def location(self, item):
        return reverse(item)

    def get_urls(self, page=1, site=None, **kwargs):
        # Use SITE_DOMAIN from settings instead of the DB sites table
        from django.contrib.sites.models import Site as DjangoSite
        try:
            site = DjangoSite(domain=_DOMAIN, name='BengalBound')
        except Exception:
            pass
        return super().get_urls(page=page, site=site, **kwargs)

    def priority(self, item):
        if item == 'public_site:home':
            return 1.0
        if item in ('public_site:pricing', 'public_site:ai_job_portal'):
            return 0.95
        return 0.8


class BlogSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.7
    protocol = 'https'

    def items(self):
        return BlogPost.objects.filter(is_published=True).order_by('-created_at')

    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else obj.created_at

    def location(self, obj):
        return reverse('public_site:blog_detail', kwargs={'slug': obj.slug})
