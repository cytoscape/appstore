from django.contrib import admin
from apps.models import (
    App, Author, Release, ReleaseAPI, Screenshot, Tag, ServiceAppMetadata,
)


class ServiceAppMetadataInline(admin.StackedInline):
    model = ServiceAppMetadata
    extra = 0
    readonly_fields = ('health_status', 'last_health_check')
    fields = (
        'service_url',
        'service_spec_version',
        'registration_validated',
        'health_status',
        'last_health_check',
    )


@admin.register(App)
class AppAdmin(admin.ModelAdmin):
    list_display = ('name', 'fullname', 'app_type', 'active', 'latest_release_date')
    list_filter = ('app_type', 'active', 'featured')
    search_fields = ('name', 'fullname', 'description')
    inlines = [ServiceAppMetadataInline]

    def get_inline_instances(self, request, obj=None):
        # Only render the ServiceAppMetadata inline for service-type apps
        if obj and obj.app_type == 'service':
            return super().get_inline_instances(request, obj)
        return []


admin.site.register(Tag)
admin.site.register(Screenshot)
admin.site.register(Author)
admin.site.register(Release)
admin.site.register(ReleaseAPI)
