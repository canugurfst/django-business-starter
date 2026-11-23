from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .emails import notify_contact_message
from .forms import ContactForm
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


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            if not form.is_spam():
                msg = form.save()
                msg.email_sent = notify_contact_message(msg)
                msg.save(update_fields=["email_sent"])
            # Bots get the same success response, so they learn nothing.
            messages.success(request, "Thank you, your message has been sent. We will get back to you soon.")
            # Redirect after POST so refreshing the page does not resubmit.
            return redirect("core:contact")
    else:
        form = ContactForm()
    return render(request, "core/contact.html", {"form": form})


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
