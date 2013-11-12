# when a 500 error occurs, each ADMIN receives an email of the backtrace
ADMINS = (
    ('Samad Lotia', 'samad.lotia@gladstone.ucsf.edu'),
)

# when a broken link occurs, each MANAGER receives a notification
MANAGERS = ADMINS

# django.core.mail.send_mail function doesn't accept the ADMINS variable;
# it requires a list of only emails instead. CONTACT_EMAILS strips off
# the names and returns a list of emails.
CONTACT_EMAILS = [a[1] for a in ADMINS]

# used for the from: field in emails
CONTACT_EMAIL = CONTACT_EMAILS[0]


# settings for sending emails (i.e., 500 errors, "Contact Us" form)
EMAIL_USE_TLS       = True
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_HOST_USER     = 'cytoscape.app.store'
EMAIL_ADDR          = EMAIL_HOST_USER  + '@gmail.com'
EMAIL_HOST_PASSWORD = ''
