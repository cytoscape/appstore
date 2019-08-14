import xml.etree.ElementTree as ET
import re

_NsTagRE = re.compile(r'\{([^\}]+)\}(.+)')
def _parse_ns_tag(ns_tag):
    m = _NsTagRE.match(ns_tag)
    return m.groups() if m else (None, None)

def _mk_tag(ns, tag):
    return '{%s}%s' % (ns, tag) if ns else tag

def _get_value(root, ns, tag):
    elem = root.find(_mk_tag(ns, tag))
    return elem.text if elem != None else None

PomAttrNames = ('groupId', 'artifactId', 'version')

def parse_pom(inputfile):
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
