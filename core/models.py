"""
Content the site owner edits in the Django admin.

- SiteSettings: one row of business details (name, contact info) shown on every page.
- Page: simple content pages (About, Privacy, ...), each with its own URL and SEO fields.
- Service: the offerings a small business lists, with a detail page each.

Everything has `is_published` / `order` so the owner can hide or reorder items
without deleting anything or asking a developer.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


class SiteSettings(models.Model):
    """Singleton: there is only ever one row, edited from the admin."""

    site_name = models.CharField(max_length=100, default="Example Business")
    tagline = models.CharField(max_length=200, blank=True)
    default_meta_description = models.CharField(
        max_length=160, blank=True,
        help_text="Used on pages without their own description. Keep under 160 characters.",
    )
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    address = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "site settings"
        verbose_name_plural = "site settings"

    def __str__(self):
        return self.site_name

    def clean(self):
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError("Site settings already exist; edit the existing entry.")

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


RESERVED_PAGE_SLUGS = {"services", "contact", "admin", "static", "media"}


class PublishedQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)


class SeoFields(models.Model):
    """Per-object SEO overrides, shared by Page and Service."""

    meta_title = models.CharField(
        max_length=70, blank=True,
        help_text="Browser tab / search result title. Defaults to the title.",
    )
    meta_description = models.CharField(
        max_length=160, blank=True,
        help_text="Search result snippet. Keep under 160 characters.",
    )

    class Meta:
        abstract = True


class Page(SeoFields):
    title = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, help_text="The URL: /<slug>/")
    body = models.TextField(help_text="Plain text; blank lines start new paragraphs.")
    show_in_nav = models.BooleanField(default=True)
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PublishedQuerySet.as_manager()

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title

    def clean(self):
        # Pages live at /<slug>/, so they must not collide with fixed URLs.
        if self.slug in RESERVED_PAGE_SLUGS:
            raise ValidationError({"slug": f"'{self.slug}' is already used by the site. Choose another."})

    def get_absolute_url(self):
        return reverse("core:page_detail", args=[self.slug])


class Service(SeoFields):
    title = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, help_text="The URL: /services/<slug>/")
    summary = models.CharField(max_length=255, help_text="One or two sentences for the services list.")
    body = models.TextField(help_text="Plain text; blank lines start new paragraphs.")
    image = models.ImageField(upload_to="services/", blank=True)
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PublishedQuerySet.as_manager()

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:service_detail", args=[self.slug])


class ContactMessage(models.Model):
    """Every contact form submission is stored before the email is sent,
    so a message is never lost if the email provider is down."""

    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    message = models.TextField(max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)
    is_handled = models.BooleanField(default=False, help_text="Tick once you have replied.")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} <{self.email}>"
