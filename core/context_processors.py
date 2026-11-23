import json

from django.conf import settings

from .models import Page, SiteSettings

# Same escaping Django's json_script uses, so content typed in the admin
# cannot close the <script> tag.
_JSON_ESCAPES = {ord("<"): r"\u003C", ord(">"): r"\u003E", ord("&"): r"\u0026"}


def site(request):
    """Business details, nav links and SEO values, available in every template."""
    site_settings = SiteSettings.load()
    base_url = settings.SITE_URL.rstrip("/") or request.build_absolute_uri("/").rstrip("/")

    structured = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": site_settings.site_name,
        "url": base_url + "/",
    }
    if site_settings.email:
        structured["email"] = site_settings.email
    if site_settings.phone:
        structured["telephone"] = site_settings.phone
    if site_settings.address:
        structured["address"] = site_settings.address

    return {
        "site": site_settings,
        "nav_pages": Page.objects.published().filter(show_in_nav=True).only("title", "slug"),
        "canonical_url": base_url + request.path,
        "structured_data": json.dumps(structured, ensure_ascii=False).translate(_JSON_ESCAPES),
    }
