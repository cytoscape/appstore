from django.core.management.base import BaseCommand
from submit_app.models import ServiceAppPending
from submit_app.servicechecker import check_metadata, ServiceCheckError

class Command(BaseCommand):
    help = "Process and validate service apps"

    def handle(self, *args, **kwargs):

        pending_apps = ServiceAppPending.objects.filter(status=ServiceAppPending.Status.PENDING)
        for app in pending_apps:
            try:
                metadata = fetch_metadata(app.service_endpoint)
                app.metadata = metadata
                app.name = metadata.get('name', app.fullname)
                app.version = metadata.get('version', app.version)
                app.status = ServiceAppPending.Status.VALIDATED
                app.validation_error = ""
            except ServiceCheckError as e:
                app.status = ServiceAppPending.Status.FAILED
                app.validation_error = str(e)
            app.save()
