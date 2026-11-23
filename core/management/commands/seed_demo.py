"""Fill an empty database with placeholder content so the site is not blank.

Safe to run repeatedly: existing rows (matched by slug) are left untouched,
so edits made in the admin are never overwritten.
"""

from django.core.management.base import BaseCommand

from core.models import Page, Service, SiteSettings

PAGES = [
    {"slug": "about", "title": "About us", "order": 1,
     "body": "We are a small, independent business.\n\nThis text is placeholder content. Edit it in the admin under Pages."},
    {"slug": "privacy", "title": "Privacy policy", "order": 9, "show_in_nav": False,
     "body": "Describe what personal data the contact form collects and how it is used."},
]

SERVICES = [
    {"slug": "consulting", "title": "Consulting", "order": 1,
     "summary": "An example service. Replace it with a real offering.",
     "body": "Explain who this service is for, what is included, and what the client gets at the end."},
    {"slug": "training", "title": "Training", "order": 2,
     "summary": "A second example service, so the list looks like a list.",
     "body": "Services can be hidden, reordered or rewritten from the admin without touching code."},
]


class Command(BaseCommand):
    help = "Create placeholder site settings, pages and services if they do not exist."

    def handle(self, *args, **options):
        settings = SiteSettings.load()
        if not settings.tagline:
            settings.tagline = "A short line about what the business does."
            settings.default_meta_description = "Example Business: placeholder description for search engines."
            settings.email = "hello@example.com"
            settings.save()

        created = 0
        for model, rows in ((Page, PAGES), (Service, SERVICES)):
            for row in rows:
                data = dict(row)
                _, was_created = model.objects.get_or_create(slug=data.pop("slug"), defaults=data)
                created += was_created
        if options["verbosity"]:
            self.stdout.write(f"seed_demo: {created} item(s) created.")
