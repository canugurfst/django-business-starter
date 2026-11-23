from .models import Page, SiteSettings


def site(request):
    """Business details and nav links, available in every template."""
    return {
        "site": SiteSettings.load(),
        "nav_pages": Page.objects.published().filter(show_in_nav=True).only("title", "slug"),
    }
