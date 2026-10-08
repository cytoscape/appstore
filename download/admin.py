from django.contrib import admin
from download.models import *

admin.site.register(GeoLoc)
admin.site.register(ReleaseDownloadsByDate)
admin.site.register(AppDownloadsByGeoLoc)
admin.site.register(WebBundleDownload)
admin.site.register(ServiceDownload)
admin.site.register(Download)
admin.site.register(ServiceReleaseDownloadsByDate)
admin.site.register(WebBundleReleaseDownloadsByDate)
