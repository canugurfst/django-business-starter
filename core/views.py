from django.shortcuts import get_object_or_404, render

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
