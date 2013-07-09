# settings for GeoIP

from os.path import join as filejoin, abspath
from paths import SITE_DIR

# the download/geolite directory has a Makefile that automatically downloads
# the latest GeoLite data files
GEOIP_PATH = abspath(filejoin(SITE_DIR, 'download', 'geolite'))

# the absolute path to the GeoIP library file; ends in *.dylib on Mac, or *.a on Linux
GEOIP_LIBRARY_PATH = '' 
