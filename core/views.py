from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import Page, Service


def home(request):
    return render(request, "core/home.html", {"services": Service.objects.published()})


def service_list(request):
    return render(request, "core/service_list.html", {"services": Service.objects.published()})


def service_detail(request, slug):
    service = get_object_or_404(Service.objects.published(), slug=slug)
    return render(request, "core/service_detail.html", {"service": service})


def page_detail(request, slug):
    page = get_object_or_404(Page.objects.published(), slug=slug)
    return render(request, "core/page_detail.html", {"page": page})


def robots_txt(request):
    if settings.SITE_NOINDEX:
        lines = ["User-agent: *", "Disallow: /"]
    else:
        # The admin path is deliberately not listed here: robots.txt is
        # public, and listing it would advertise the URL we keep private.
        lines = [
            "User-agent: *",
            "Allow: /",
            "",
            f"Sitemap: {request.build_absolute_uri(reverse('sitemap'))}",
        ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")
