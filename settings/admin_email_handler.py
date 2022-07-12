from django.utils.log import AdminEmailHandler
from django.core import mail

# extends default admin email handler
class CustomEmailHandler(AdminEmailHandler):
    def send_mail(self, subject, message, *args, **kwargs):
        # set fail_silently true before proceeding
        kwargs["fail_silently"] = False
        return super().send_mail(subject, message, *args, **kwargs)
