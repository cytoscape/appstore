# settings for xapian indexing

from os.path import join as filejoin
try:
    from conf.paths import SITE_DIR
except ImportError:
    from conf.mock import SITE_DIR
XAPIAN_INDICES_DIR = filejoin(SITE_DIR, 'xapian_indices')
