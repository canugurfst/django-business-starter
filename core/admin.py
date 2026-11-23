from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse

from .models import Page, Service, SiteSettings

admin.site.site_header = "Site administration"
admin.site.site_title = "Site admin"
admin.site.index_title = "Edit your website"

SEO_FIELDSET = ("Search engines", {
    "fields": ("meta_title", "meta_description"),
    "classes": ("collapse",),
    "description": "Optional. Leave empty to use the title and the site-wide description.",
})


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Skip the list view: 'Site settings' opens the single entry directly."""

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = SiteSettings.load()
        return redirect(reverse("admin:core_sitesettings_change", args=[obj.pk]))


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "show_in_nav", "is_published", "order", "updated_at")
    list_editable = ("show_in_nav", "is_published", "order")
    search_fields = ("title", "body")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (None, {"fields": ("title", "slug", "body")}),
        ("Display", {"fields": ("show_in_nav", "is_published", "order")}),
        SEO_FIELDSET,
    )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published", "order", "updated_at")
    list_editable = ("is_published", "order")
    search_fields = ("title", "summary", "body")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (None, {"fields": ("title", "slug", "summary", "body", "image")}),
        ("Display", {"fields": ("is_published", "order")}),
        SEO_FIELDSET,
    )
