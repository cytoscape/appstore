from django import forms


class ServiceAppSubmitForm(forms.Form):
    service_url = forms.URLField(
        label="Service base URL",
        help_text="Example: https://example.org/myservice"
    )
