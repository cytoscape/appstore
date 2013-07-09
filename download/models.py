from django.db.models import Model, CharField, PositiveIntegerField, ForeignKey, DateField
from apps.models import App, Release

class Download(Model):
    release = ForeignKey(Release, related_name='app_download_stats')
    when    = DateField()
    ip4addr = PositiveIntegerField()

class ReleaseDownloadsByDate(Model):
    release = ForeignKey(Release, null = True) # null release has total count across a given day
    when    = DateField()
    count   = PositiveIntegerField(default = 0)

    def __str__(self):
        return '%s - %s: %d' % (self.release, self.date, self.count)

class GeoLoc(Model):
    country = CharField(max_length = 2) # when region & city are empty, country contains the total
    region  = CharField(max_length = 2,  blank = True)
    city    = CharField(max_length = 63, blank = True)

    def __str__(self):
        return '%s %s %s' % (self.country, self.region, self.city)

class AppDownloadsByGeoLoc(Model):
    app    = ForeignKey(App, null = True) # null app has total count across a given geoloc
    geoloc = ForeignKey(GeoLoc)
    count  = PositiveIntegerField(default = 0)

    def __str__(self):
        return '%s - %s: %d' % (self.app, self.geoloc, self.count)
