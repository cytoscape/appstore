"""
Config Mock to run server if real config settings are missing.
"""

import warnings
warnings.warn("Running with local config MOCK !")


MVN_BIN_PATH = ""
MVN_SETTINGS_PATH = ""
EMAIL_ADDR = ""
SITE_DIR = "/tmp/"
SITE_URL = "http://localhost"
SECRET_KEY = "12345"
GEOIP_PATH = "/tmp/"