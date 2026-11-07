import functools
import subprocess

from django.conf import settings

# shown when git can't say which code is running
UNKNOWN_VERSION = 'develop'

_GIT_TIMEOUT_S = 5


def _git(*args):
    """The output of 'git args' in the code's checkout, or None if git fails."""
    try:
        result = subprocess.run(['git', *args], cwd=settings.BASE_DIR, capture_output=True, text=True,
                                timeout=_GIT_TIMEOUT_S)
    except (OSError, subprocess.SubprocessError):
        return None
    output = result.stdout.strip()
    return output if result.returncode == 0 and output else None


@functools.lru_cache(maxsize=None)
def app_version():
    """
    The running code's version, from its git checkout: the tag HEAD is at, else HEAD's
    abbreviated commit hash, else 'develop'. Worked out once per server process; a
    deploy restarts the process.
    """
    return (_git('describe', '--tags', '--exact-match', 'HEAD')
            or _git('rev-parse', '--short', 'HEAD')
            or UNKNOWN_VERSION)
