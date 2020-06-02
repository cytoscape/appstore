from django.db.models import Model, CharField, PositiveIntegerField
from django.db.models import ForeignKey, DateField
from apps.models import App, Release
from django.db import models
from util.view_util import ipaddr_long_to_str


class Download(Model):
    release = ForeignKey(Release, related_name='app_download_stats',
                         on_delete=models.CASCADE)
    when = DateField()
    ip4addr = PositiveIntegerField()

    def __unicode__(self):
        return unicode(self.release) + u' ' + unicode(self.when) +\
               u' ' + ipaddr_long_to_str(self.ip4addr)


class ReleaseDownloadsByDate(Model):
    release = ForeignKey(Release, on_delete=models.CASCADE,
                         null=True)  # null release has total count across a given day
    when = DateField()
    count = PositiveIntegerField(default=0)

    def __unicode__(self):
        return unicode(self.release) + u' ' + unicode(self.when) + u': ' +\
               unicode(self.count)


class GeoLoc(Model):
    country = CharField(max_length=2)  # when region & city are empty, country contains the total
    region = CharField(max_length=2,  blank=True)
    city = CharField(max_length=63, blank=True)

    def __unicode__(self):
        return self.country + u' ' + self.region + u' ' + self.city


class AppDownloadsByGeoLoc(Model):
    app = ForeignKey(App, null=True, on_delete=models.CASCADE)  # null app has total count across a given geoloc
    geoloc = ForeignKey(GeoLoc, on_delete=models.CASCADE)
    count = PositiveIntegerField(default=0)

    def __unicode__(self):
        return unicode(self.app) + u' ' + unicode(self.geoloc) + u': ' +\
               unicode(self.count)
