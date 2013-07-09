# when a 500 error occurs, each ADMIN receives an email of the backtrace
ADMINS = (
    ('Samad Lotia', 'samad.lotia@gladstone.ucsf.edu'),
)

# when a broken link occurs, each MANAGER receives a notification
MANAGERS = ADMINS

# when users fill out the "Contact Us" form, this person receives an email
CONTACT_EMAIL = 'samad.lotia@gladstone.ucsf.edu'

# settings for sending emails (i.e., 500 errors, "Contact Us" form)
EMAIL_USE_TLS       = True
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_HOST_USER     = 'cytoscape.app.store'
EMAIL_ADDR          = EMAIL_HOST_USER  + '@gmail.com'
EMAIL_HOST_PASSWORD = ''
