from django.contrib import admin
from download.models import *

admin.site.register(GeoLoc)
admin.site.register(ReleaseDownloadsByDate)
admin.site.register(AppDownloadsByGeoLoc)
