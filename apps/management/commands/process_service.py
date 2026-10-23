from django.core.management.base import BaseCommand
from submit_app.models import ServiceAppPending
from submit_app.servicechecker import check_reachable, check_service_status, ServiceCheckError
import requests
from django.core.mail import send_mail
from django.conf import settings

VALID_CY_WEB_ACTIONS = {
    'addNetworks', 'updateNetwork', 'addTables',
    'updateTables', 'updateLayouts', 'updateSelection', 'openURL'
}

def validate_metadata(metadata):
    errors = [] #empty list means all checks passed

    for field in ('name', 'version', 'author'):
        if not metadata.get(field):
            errors.append(f'Missing field: {field}')
        
    cy_actions = metadata.get('CyWebActions')
    if cy_actions is not None:
        invalid = [a for a in cy_actions if a not in VALID_CY_WEB_ACTIONS]
        if invalid:
            errors.append(f'Invalid Action: {invalid}')

    if not isinstance(metadata.get('serviceInputDefinition'), dict):
        errors.append('serviceInputDefinition must be a JSON object')
    
    params = metadata.get('parameters')
    if params is not None and not isinstance(params, list):
        errors.append('parameters must be a list')

    return errors

class Command(BaseCommand):
    help = 'Validate pending service app submissions'

    def handle(self, *args, **options):
        pending_apps = ServiceAppPending.objects.filter(status=ServiceAppPending.Status.PENDING_CHECKER)

        for pending in pending_apps:
            errors = []
            self.stdout.write(f'Checking {pending.fullname} ({pending.service_endpoint})')
            try:
                metadata = check_reachable(pending.service_endpoint)
            except ServiceCheckError as e:
                errors.append(f'Reachability check failed: {e}')
                pending.status = ServiceAppPending.Status.CHECKER_FAILED    
                pending.metadata = {**(pending.metadata or {}), 'check_errors': errors}
                pending.save()
                continue

            try:
                status = check_service_status(pending.service_endpoint)
                if status.get('status') != 'ok':
                    stat = status.get('status')
                    errors.append(f'Service returned non-ok status: {stat}')
            except ServiceCheckError as e:
                errors.append(f'Status check failed: {e}')
            
            errors.extend(validate_metadata(metadata))

            if metadata.get('name') != pending.fullname:
                errors.append(f"Name in metadata ({metadata.get('name')!r}) does not match submitted name ({pending.fullname!r})")

            if metadata.get('version') != pending.version:
                errors.append(f"Name in metadata ({metadata.get('version')!r}) does not match submitted name ({pending.version!r})")

            if errors:
                pending.status = ServiceAppPending.Status.CHECKER_FAILED
                pending.metadata = {**(pending.metadata or {}), 'check_errors': errors}
                self.stdout.write(self.style.ERROR(f'  FAILED: {errors}'))

                submitter_email = getattr(pending.submitter, 'email', None)
                if submitter_email:
                    subject = f"Service submission '{pending.fullname}' failed automated checks"
                    body_lines = [
                        f"Your submission '{pending.fullname}' ({pending.service_endpoint}) failed the automated checker.",
                        '',
                        'Problems Found:',
                    ] + [f"- {e}" for e in errors] + [
                        '',
                        'Please fix the issues above and resubmit at https://apps.cytoscape.org/submit_app/service',
                        '',
                        '- Cytoscape App Store Team',
                        f"Contact: {getattr(settings, 'CONTACT_EMAIL', 'no-reply')}"
                    ]
                    body = '\n'.join(body_lines)

                    try:
                        send_mail(subject, body, getattr(settings, 'CONTACT_EMAIL', None), [submitter_email], fail_silently=False)
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Failed to send email to {submitter_email}: {e}'))

                pending.delete()
            else:
                pending.status = ServiceAppPending.Status.PENDING_REVIEW
                pending.metadata = {**(pending.metadata or {}), 'check_errors': []}
                self.stdout.write(self.style.SUCCESS(f'  CHECKER PASSED. TO BE REVIEWED MANUALLY'))
                pending.save()