import xml.etree.ElementTree as ET
import re

_NsTagRE = re.compile(r'\{([^\}]+)\}(.+)')
"""
Regex used to parse namespace
"""


PomAttrNames = ('groupId', 'artifactId', 'version')
"""
Attribute names to parse from pom file
used by parse_pom() function
"""


def _parse_ns_tag(ns_tag):
    """
    Assumes input is {text...}xxx and returns
    the content between the curly braces ie text...

    :param ns_tag:
    :return: (content between curly braces) or (None, None)
             if no group of curly braces are found
    :rtype: tuple
    """
    m = _NsTagRE.match(ns_tag)
    return m.groups() if m else (None, None)


def _mk_tag(ns, tag):
    """
    If 'ns' is not None this function puts curly braces
    around it and appends value of 'tag' otherwise value of
    'tag' is returned

    :param ns: namespace
    :param tag:
    :return: {ns}tag or tag if ns is None
    :rtype: str
    """
    return '{%s}%s' % (ns, tag) if ns else tag


def _get_value(root, ns, tag):
    elem = root.find(_mk_tag(ns, tag))
    if elem is None:
        return None
    return elem.text


def parse_pom(inputfile):
    """
    Parses pom file passed in

    :param inputfile:
    :return: If found, 'groupId', 'artifactId', and 'version' will be
             added to dict. if none are found and empty dict is returned
    :rtype: dict
    """
    try:
        tree = ET.parse(inputfile)
    except:
        return dict()
    root = tree.getroot()
    xmlns, _ = _parse_ns_tag(root.tag)
    parent = root.find(_mk_tag(xmlns, 'parent'))

    attrs = dict()
    for name in PomAttrNames:
        val = _get_value(root, xmlns, name)
        if val:
            attrs[name] = val
        elif parent:
            val_from_parent = _get_value(parent, xmlns, name)
            if val_from_parent:
                attrs[name] = val_from_parent
    return attrs
