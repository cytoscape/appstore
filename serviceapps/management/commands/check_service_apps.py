import json

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone

from serviceapps.models import ServiceApp


class Command(BaseCommand):
    help = "Ping /status for all active Service Apps"

    def handle(self, *args, **opts):
        for sa in ServiceApp.objects.filter(is_active=True):
            try:
                r = requests.get(
                    sa.service_url.rstrip("/") + "/status",
                    timeout=8,
                    headers={"Accept": "application/json"},
                )
                r.raise_for_status()
                data = r.json()
                sa.last_status = ("ok" if data.get("status") == "ok"
                                  else "unavailable")
                sa.last_message = ("" if sa.last_status == "ok"
                                   else json.dumps(data)[:500])
            except Exception as e:
                sa.last_status = "error"
                sa.last_message = str(e)[:500]
            sa.last_checked = timezone.now()
            sa.save()
            self.stdout.write(f"{sa.service_url} -> {sa.last_status}")
