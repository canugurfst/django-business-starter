from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Page, Service


class StaticSitemap(Sitemap):
    """Fixed URLs that are not database objects."""

    changefreq = "monthly"

    def items(self):
        return ["core:home", "core:service_list"]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1.0 if item == "core:home" else 0.7


class PageSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Page.objects.published()

    def lastmod(self, obj):
        return obj.updated_at


class ServiceSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return Service.objects.published()

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {"static": StaticSitemap, "pages": PageSitemap, "services": ServiceSitemap}
