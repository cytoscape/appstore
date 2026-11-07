from util.version import app_version as _app_version


def app_version(request):
    """Every page's footer shows the running version."""
    return {'APP_VERSION': _app_version()}
