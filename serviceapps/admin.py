from django.contrib import admin
from .models import ServiceApp


@admin.register(ServiceApp)
class ServiceAppAdmin(admin.ModelAdmin):
    list_display = ("display_name", "service_url", "last_status",
                    "last_checked", "is_active")
    list_filter = ("last_status", "is_active")
    search_fields = ("display_name", "service_url", "author", "description")
