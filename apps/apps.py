from django.apps import AppConfig
from django.db.models.signals import pre_migrate


class AppsConfig(AppConfig):
    name = 'apps'

    def ready(self):
        from apps.schema_prep import prepare_schema_before_migrate
        pre_migrate.connect(prepare_schema_before_migrate, sender=self,
                            dispatch_uid='apps.prepare_schema_before_migrate')
