from django.db import models


class ServiceApp(models.Model):
    service_url = models.URLField(unique=True, help_text="Base URL of the service")
    metadata = models.JSONField(default=dict, blank=True)

    display_name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    author = models.CharField(max_length=255, blank=True)
    version = models.CharField(max_length=64, blank=True)

    is_active = models.BooleanField(default=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(max_length=32, default="unknown")
    last_message = models.TextField(blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_name", "service_url"]
        indexes = [
            models.Index(fields=["is_active", "last_status"]),
            models.Index(fields=["display_name"]),
        ]

    def __str__(self):
        return self.display_name or self.service_url

    def as_app_definition(self):
        return {"url": self.service_url}
