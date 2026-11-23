from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("services/", views.service_list, name="service_list"),
    path("services/<slug:slug>/", views.service_detail, name="service_detail"),
    path("contact/", views.contact, name="contact"),
    # Catch-all for admin-created pages; keep it last.
    path("<slug:slug>/", views.page_detail, name="page_detail"),
]
