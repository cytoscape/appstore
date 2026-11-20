from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

# the unique key apps.cytoscape.org's apps_orderedauthor kept from its apps_app_authors days (#160)
LEGACY_AUTHOR_KEY = 'ALTER TABLE `apps_orderedauthor` ADD UNIQUE KEY `app_id` (`app_id`, `author_id`)'


class Command(BaseCommand):
    help = ("Gives apps_orderedauthor the old unique key on (app_id, author_id) that apps.cytoscape.org's "
            "database has, so the integration suite's database is in prod's state before the deploy's "
            "migrate (#160). Runs only where settings.INTEGRATION_SEED_ENABLED is True, on MySQL/MariaDB.")

    def handle(self, *args, **options):
        if not getattr(settings, 'INTEGRATION_SEED_ENABLED', False):
            raise CommandError('add_legacy_author_key changes the schema; it runs only with INTEGRATION_SEED_ENABLED')
        if connection.vendor != 'mysql':
            raise CommandError('add_legacy_author_key needs MySQL/MariaDB, not %s' % connection.vendor)
        with connection.cursor() as cursor:
            cursor.execute(LEGACY_AUTHOR_KEY)
        self.stdout.write('Added the legacy key: %s' % LEGACY_AUTHOR_KEY)
