from apps.models import VersionRE
from collections import defaultdict

# This file contains functions for parsing manifest files.

# Parses a manifest file into a dictionary.
#
# The manifest file follows this format:
# key1: val1
# key2: val2
# key3: a
#  b
#  c
# key2: val4
#
# This method would return this multi-value dictionary:
# {'key1': ['val1'],
#  'key2': ['val2', 'val4'],
#  'key3': ['abc']}
#
# Manifest files have continuations, which allow a value to
# be split across multiple lines. A continuation is denoted
# by a single space at the beginning of the line. key3's
# value is a continuation.
#
# Arguments:
#  manifest_lines: an iterable of the lines in the manifest file
# Returns:
#  a dictionary representing the contents of of the manifest file.
def parse_manifest(manifest_lines):
    keys = list()
    vals = list()
    for line in manifest_lines:
        if not line.strip(): continue # ignore empty lines
        line = line.splitlines()[0]
        if line.startswith(b' '): # is this line a continuation?
            if not vals: continue # if we haven't read any entries, ignore this continuation
            vals[-1] += line[1:] # add the continuation to the last value
        else:
            (key, _, val) = line.partition(b':')
            keys.append(key.strip())
            vals.append(val.strip())
    return _multival_dict(zip(keys, vals))

def _multival_dict(keysAndVals):
    d = defaultdict(list)
    for k, v in keysAndVals:
        d[k].append(v)
    return dict(d)

# ---------------------------------------------------

# This section of code deals with parsing the Import-Package manifest entry
# that has a particular syntax. Here's what Import-Package might look like:
#   a.b.c,d.e.f;resolution:=False,h.i.j;version=1.2.3.beta,l.m.n;version="(1.2,3]"
# As you can see above, package names are separated by a ",". A package could
# have additional attributes, separated by a ";". The version attribute
# could take the form of a version range, which has this syntax:
#   "("|"[" + lower-version + "," + upper-version + ")"|"]"
# The problem with parsing Import-Package is that we can't just split the string by ",".
# This is because the version attribute could have a "," if it's a version range. The 
# function _index_of_char is used to split the string by "," while ignoring any commas
# surrounded by quotes.

# Searches for the index of a character in a string.
# This function recognizes double-quoted strings, so
# it won't return the character's index if it's
# in a double-quoted string. It's smart enough
# to understand escaped double-quotes.
#
# Arguments:
#  string: the string to search
#  c: the character to search in the string
# Returns:
#  returns the index of the character, or the string's length
#  if the character could not be found--this unusual
#  behavior fits well with array slices
def _index_of_char(string, c):
    i = 0
    strlen = len(string)
    while i < strlen:
        if string[i] == c:
            break
        elif _is_dblquote(string, i):
            i += 1 # we're at a ", skip over it
            while i < strlen and not _is_dblquote(string, i): # keep looping until we hit a "
                i += 1
            i += 1 # skip over the terminating "
        else:
            i += 1
    return i

def _is_dblquote(string, i):
    return string[i] == '"' and string[i - 1] != '\\'

def _split_by_pkg(s):

    return _split_by_char(s, ',')

# Takes a string and splits it by a given char. This will not split the string
# by the char if it's enclosed in double quotes.
# Arguments:
#  s: the string holding the entire "Import-Package" value.
#  c: the character to split it by
def _split_by_char(s, c):
    while s:
        next_index = _index_of_char(s, c)
        yield s[:next_index]
        s = s[next_index + 1:]

# Takes a single package string, as returned by _split_by_pkg,
# and returns the package name and a dictionary of all the attributes
# of that package string.
# A package string looks like this:
#  x.y.z;key1=val1;key2=val2
# Arguments:
#  s: a single package string, as returned by _split_by_pkg
# Returns:
#  (pkg-name, pkg-attrs), pkg-attrs is an empty dict if there are no attributes
def _extract_pkg_and_attrs(s):
    s = s.strip()
    start_index = _index_of_char(s, ';') + 1
    if start_index < len(s):
        pkg_name = s[:start_index - 1]
        attrs = dict(_extract_attrs(s[start_index:]))
        return (pkg_name, attrs)
    else:
        return (s, dict())

# Takes a string with this format:
#  key1=val1;key2=val2
# and returns this:
#  ('key1', 'val1'), ('key2', 'val2')
def _extract_attrs(s):
    while s:
        next_index = _index_of_char(s, ';')
        (name, _, val) = s[:next_index].partition('=')
        yield (name, val)
        s = s[next_index + 1:]

# A convenience method for parsing a version string into a tuple.
# It takes the following strings and returns:
#  '3.0.0.beta' => ('3', '0', '0', 'beta')
#  '3.0'        => ('3', '0', None, None)
#  '3'          => ('3', None, None, None)
#  'blah'       => None
def _parse_version(s):
    matched = VersionRE.match(s)
    if not matched:
        return None
    return matched.groups()

# Given a string representing either a version ('3.0') or a version range ('(3.0,4]'),
# returns lower version of the range, or just the parsed version itself.
def _lower_version(s):
    if ',' in s:
        return _parse_version_range(s)[1]
    else:
        return _parse_version(s)


# Parses a version range.
# Arguments:
#  s: a version range string
# Returns:
#  (start-range, start-version, end-version, end-range)
# Example:
#  '(3.0,4]' => ('(', ('3', '0', None, None), ('4', None, None, None), ']')
def _parse_version_range(s):
    no_quotes = s[1:-1]
    (start, _, end) = no_quotes.partition(',')

    if start[0] == '[' or start[0] == '(':
        start_range = start[0]
        start_ver = _parse_version(start[1:])
    else:
        start_range = '['
        start_ver = _parse_version(start)

    if end[-1] == ']' or end[-1] == ')':
        end_range = end[-1]
        end_ver = _parse_version(end[:-1])
    else:
        end_range = ')'
        end_ver = _parse_version(end)

    return (start_range, start_ver, end_ver, end_range)

# Given a string containing the 'Import-Package' value,
# returns a generator containing all the versions of
# packages whose names begin with 'org.cytoscape'.
def _lower_cytoscape_pkg_versions(s):
    for (pkgname, attrs) in map(_extract_pkg_and_attrs, _split_by_pkg(s)):
        if not 'version' in attrs or not pkgname.startswith('org.cytoscape'):
            continue
        yield _lower_version(attrs['version'])

# Given a string containing the 'Import-Package' value,
# returns the maximum version across all the lower
# versions of 'org.cytoscape.*' packages.
# Returns None if there are no Cytoscape packages.
def max_of_lower_cytoscape_pkg_versions(s):
    try:
        return max(_lower_cytoscape_pkg_versions(s))
    except ValueError:
        return None

# ---------------------------------------------------

def parse_app_dependencies(s):
    for dependency in _split_by_pkg(s):
        div_i = _index_of_char(dependency, ';')
        app_name = dependency[:div_i].strip()
        if app_name and app_name[0] == '"' and app_name[-1] == '"':
            app_name = app_name[1:-1]
        if not app_name:
            raise ValueError('no app name specified')
        app_version_str = dependency[div_i + 1:].strip()
        if not app_version_str:
            raise ValueError('app "%s" has no version specified' % app_name)
        app_version = _parse_version(app_version_str)
        if not app_version:
            raise ValueError('app %s has an invalid version: "%s"' % (app_name, app_version_str))
        yield (app_name, app_version_str)
