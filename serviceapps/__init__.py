import sys

# manage.py adds '..' to sys.path and the project root has __init__.py,
# making this package importable as both 'serviceapps' and
# 'appstore.serviceapps'. Canonicalize to the short name so Django
# does not register models twice.
_CANONICAL = 'serviceapps'
if __name__ != _CANONICAL and _CANONICAL in sys.modules:
    sys.modules[__name__] = sys.modules[_CANONICAL]
    for _key in list(sys.modules):
        if _key.startswith(_CANONICAL + '.'):
            _alt = __name__ + _key[len(_CANONICAL):]
            if _alt not in sys.modules:
                sys.modules[_alt] = sys.modules[_key]
