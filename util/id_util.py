import re

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
