import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

from django.core import mail
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ContactMessage, Page, Service

BASE_DIR = Path(__file__).resolve().parent.parent

# Tests run the same whether DEBUG is on (local .env) or off (CI): plain static
# storage so templates render without collectstatic, and no HTTPS redirect for
# the test client.
TEST_SETTINGS = dict(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
    SECURE_SSL_REDIRECT=False,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    CONTACT_EMAIL="owner@example.com",
    SITE_URL="",
    SITE_NOINDEX=False,
    CANONICAL_HOST="",
)


@override_settings(**TEST_SETTINGS)
class SiteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)


class PageTests(SiteTestCase):
    def test_public_pages_render(self):
        urls = [
            reverse("core:home"),
            reverse("core:service_list"),
            reverse("core:service_detail", args=["consulting"]),
            reverse("core:page_detail", args=["about"]),
            reverse("core:contact"),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_unpublished_content_is_hidden(self):
        Service.objects.filter(slug="consulting").update(is_published=False)
        Page.objects.filter(slug="about").update(is_published=False)
        self.assertEqual(self.client.get("/services/consulting/").status_code, 404)
        self.assertEqual(self.client.get("/about/").status_code, 404)
        self.assertNotContains(self.client.get("/services/"), "Consulting")

    def test_unknown_url_404(self):
        self.assertEqual(self.client.get("/does-not-exist/").status_code, 404)

    def test_reserved_page_slug_rejected(self):
        page = Page(title="Services", slug="services", body="x")
        with self.assertRaises(ValidationError):
            page.full_clean()

    def test_seed_is_idempotent_and_keeps_edits(self):
        from .models import SiteSettings
        Service.objects.filter(slug="consulting").update(title="Edited in admin")
        SiteSettings.objects.filter(pk=1).update(tagline="")
        call_command("seed_demo", verbosity=0)
        self.assertEqual(Service.objects.count(), 2)
        self.assertEqual(Service.objects.get(slug="consulting").title, "Edited in admin")
        self.assertEqual(SiteSettings.load().tagline, "")


class SeoTests(SiteTestCase):
    def test_meta_tags(self):
        Service.objects.filter(slug="consulting").update(meta_description="Custom snippet")
        html = self.client.get("/services/consulting/").content.decode()
        self.assertIn('<meta name="description" content="Custom snippet">', html)
        self.assertIn('<link rel="canonical" href="http://testserver/services/consulting/">', html)
        self.assertIn('"@type": "LocalBusiness"', html)

    @override_settings(SITE_URL="https://example.com")
    def test_canonical_uses_site_url(self):
        self.assertContains(self.client.get("/about/"), 'href="https://example.com/about/"')

    def test_structured_data_cannot_break_out_of_script(self):
        from .models import SiteSettings
        SiteSettings.objects.filter(pk=1).update(site_name="</script><script>alert(1)</script>")
        html = self.client.get("/").content.decode()
        self.assertNotIn("</script><script>alert(1)", html)

    def test_sitemap_lists_published_only(self):
        Service.objects.filter(slug="training").update(is_published=False)
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/services/consulting/")
        self.assertContains(response, "/contact/")
        self.assertNotContains(response, "/services/training/")

    def test_robots_points_to_sitemap(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertContains(response, "Sitemap: http://testserver/sitemap.xml")
        self.assertNotIn("X-Robots-Tag", response.headers)

    @override_settings(SITE_NOINDEX=True)
    def test_noindex_mode_blocks_crawlers(self):
        self.assertContains(self.client.get("/robots.txt"), "Disallow: /\n")
        self.assertEqual(self.client.get("/")["X-Robots-Tag"], "noindex, nofollow")

    def test_canonical_host_redirect(self):
        with self.settings(CANONICAL_HOST="example.com", ALLOWED_HOSTS=[".example.com", "notexample.com"]):
            # Middleware reads the setting at startup, so reload the handler.
            self.client.handler.load_middleware()
            response = self.client.get("/services/?x=1", HTTP_HOST="www.example.com")
            self.assertRedirects(
                response, "https://example.com/services/?x=1",
                status_code=301, fetch_redirect_response=False,
            )
            # A different domain that merely ends with the same letters is left alone.
            self.assertEqual(self.client.get("/", HTTP_HOST="notexample.com").status_code, 200)


class ContactFormTests(SiteTestCase):
    def post(self, **overrides):
        data = {"name": "Jane Doe", "email": "jane@example.com", "phone": "", "message": "Hello there"}
        data.update(overrides)
        return self.client.post(reverse("core:contact"), data, follow=True)

    def test_valid_message_saved_and_emailed(self):
        response = self.post()
        self.assertContains(response, "your message has been sent")
        msg = ContactMessage.objects.get()
        self.assertTrue(msg.email_sent)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["owner@example.com"])
        self.assertEqual(mail.outbox[0].reply_to, ["jane@example.com"])

    def test_invalid_message_shows_errors(self):
        response = self.post(email="not-an-email", message="")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "errorlist")
        self.assertFalse(ContactMessage.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_honeypot_drops_spam_silently(self):
        response = self.post(website="http://spam.example")
        self.assertContains(response, "your message has been sent")
        self.assertFalse(ContactMessage.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_email_failure_keeps_message(self):
        with mock.patch("core.emails.EmailMessage.send", side_effect=ConnectionError("provider down")):
            with self.assertLogs("core.emails", level="ERROR"):
                response = self.post()
        self.assertContains(response, "your message has been sent")
        self.assertFalse(ContactMessage.objects.get().email_sent)


class SettingsTests(TestCase):
    """Run settings in a fresh process, as production would load them."""

    def run_python(self, code, **env):
        full_env = {**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings", **env}
        return subprocess.run(
            [sys.executable, "-c", code], cwd=BASE_DIR, env=full_env,
            capture_output=True, text=True, timeout=60,
        )

    def test_refuses_to_start_without_secret_key(self):
        # An empty value is not overridden by a local .env file.
        result = self.run_python("import django; django.setup()", DJANGO_SECRET_KEY="")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY is not set", result.stderr)

    def test_production_passes_deploy_checks(self):
        # Two warnings are accepted on purpose:
        # W005 (HSTS includeSubDomains): a client's other subdomains may not
        #   all be on HTTPS; enable via DJANGO_HSTS_INCLUDE_SUBDOMAINS per site.
        # W021 (HSTS preload): preloading is hard to undo, so it is never a default.
        result = self.run_python(
            "import django; django.setup();"
            "from django.conf import settings;"
            "settings.SILENCED_SYSTEM_CHECKS = ['security.W005', 'security.W021'];"
            "from django.core.management import call_command;"
            "call_command('check', deploy=True, fail_level='WARNING')",
            DJANGO_SECRET_KEY="x" * 50 + "-not-a-real-key-but-long-and-varied-0123456789",
            DJANGO_DEBUG="False",
            DJANGO_HSTS_SECONDS="31536000",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
