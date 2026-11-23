from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class CanonicalHostMiddleware:
    """301-redirect alternate hosts (e.g. www.example.com) to CANONICAL_HOST.

    One canonical host means search engines see one site, not two copies.
    Disabled when CANONICAL_HOST is empty, so local dev and Railway preview
    URLs keep working.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.canonical = settings.CANONICAL_HOST.lower()

    def __call__(self, request):
        if self.canonical:
            host = request.get_host().split(":")[0].lower()
            if host != self.canonical and host.endswith("." + self.canonical):
                return HttpResponsePermanentRedirect(f"https://{self.canonical}{request.get_full_path()}")
        return self.get_response(request)


class NoIndexMiddleware:
    """Send X-Robots-Tag: noindex on every response while SITE_NOINDEX is on.

    Used on preview deployments so a half-finished site never ends up in Google.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if settings.SITE_NOINDEX:
            response["X-Robots-Tag"] = "noindex, nofollow"
        return response
