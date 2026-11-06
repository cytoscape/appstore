import enum
import re
from collections import namedtuple

from apps.models import App

_non_alphanum_re = re.compile('[\W_]+')


def fullname_to_name(fullname):
    """
    Creates str from 'fullname' where all non word
    characters are removed. Any remaining characters
    are lower cased

    :param fullname: Input str
    :type fullname: str
    :return: 'fullname' lowercased with non word characters removed
    :rtype: str
    """
    return _non_alphanum_re.sub('', fullname).lower()


class IdentityOutcome(enum.Enum):
    NEW_APP = 'new_app'                      # no app has this name yet
    NEW_PLATFORM = 'new_platform'            # the user's app, but its first release on this platform
    EXISTING_PLATFORM = 'existing_platform'  # the user's app, already released on this platform
    NOT_EDITOR = 'not_editor'                # the name belongs to an app the user cannot edit


AppIdentity = namedtuple('AppIdentity', ['name', 'app', 'outcome'])


def resolve_app_identity(fullname, user, platform):
    """
    Works out which app a submission named 'fullname' belongs to. An app is
    identified by its name alone: the same name on another platform is the
    same app, so a submission either starts a new app or adds to an existing one.

    :param fullname: app name the submission carries (jar manifest, service metadata or cy-manifest.json)
    :param user: the submitter
    :param platform: the submission's :py:class:`~apps.models.Platform`
    :return: the app's name, the existing App (None for a new app) and the :py:class:`IdentityOutcome`
    :rtype: AppIdentity
    """
    name = fullname_to_name(fullname)
    app = App.objects.filter(name=name).first()
    if app is None:
        outcome = IdentityOutcome.NEW_APP
    elif not app.is_editor(user):
        outcome = IdentityOutcome.NOT_EDITOR
    elif app.has_platform(platform):
        outcome = IdentityOutcome.EXISTING_PLATFORM
    else:
        outcome = IdentityOutcome.NEW_PLATFORM
    return AppIdentity(name, app, outcome)
