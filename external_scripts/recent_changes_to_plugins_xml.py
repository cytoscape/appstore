from xml.dom.minidom import parse
from itertools import ifilter
import re
import argparse
import sys
from urllib.request import urlopen
from datetime import date, timedelta, MINYEAR
from smtplib import SMTP

PLUGINS_XML_URL = 'http://chianti.ucsd.edu/cyto_web/plugins/plugins.xml'

def ez_elem_val(dom_obj, elem):
	tags = dom_obj.getElementsByTagName(elem)
	if not tags: return None
	return tags[0].childNodes[0].nodeValue

ISO_DATE_RE = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
def parse_iso_date(iso_date):
	if not iso_date: return None
	(year_str, month_str, day_str) = ISO_DATE_RE.match(iso_date).groups()
	(year, month, day) = (int(year_str), int(month_str), int(day_str))
	if not MINYEAR <= year:
		return None
	return date(year, month, day)

def plugins_dom_to_std_objs(dom_root):
    plugins_dom = dom_root.getElementsByTagName('plugin')

    for plugin_dom in plugins_dom:
    	plugin_obj = dict()
    	for elem in ('name', 'description', 'pluginVersion', 'release_date', 'url'):
    		plugin_obj[elem] = ez_elem_val(plugin_dom, elem)
    	if not plugin_obj['name']: continue
    	plugin_obj['release_date'] = parse_iso_date(plugin_obj['release_date'])
    	yield plugin_obj

def filter_for_recent_plugins(plugins, min_date):
	def is_plugin_recent(plugin_obj):
		d = plugin_obj['release_date']
		if not d: return False
		delta = d - min_date
		return delta.days >= 0
	return ifilter(is_plugin_recent, plugins)

def filter_for_plugins_in_n_days(plugins, n_days):
	min_date = date.today() - timedelta(n_days)
	return filter_for_recent_plugins(plugins, min_date)

def fmt_plugin(plugin):
	return '''
{name}
  - Version:
      {pluginVersion}
  - Description:
      {description}
  - Release date:
      {release_date}
  - Download:
      {url}'''.format(**plugin)

def email_msg(email_to, msg, subject):
	s = SMTP()
	s.connect('jdgmail.ucsf.edu')
	email_from = 'samad.lotia@gladstone.ucsf.edu'
	fmted_email_to = ', '.join(email_to)
	fmted_msg = 'From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s' % (email_from, fmted_email_to, subject, msg)
	s.sendmail(email_from, fmted_email_to, fmted_msg)
	s.quit()


def parse_args(args):
	parser = argparse.ArgumentParser(description='Get a list of recent plugins added to plugins.xml')
	parser.add_argument('-n', help='number of days from today', type=int, default=7)
	parser.add_argument('--email-to', help='send an email with the list of recent plugins', type=str, nargs='*')
	parsed = parser.parse_args(args)
	if not parsed: return None
	return (parsed.n, parsed.email_to)

def main(args):
    parsed_args = parse_args(args)
    if not parsed_args: return
    (n_days, email_to) = parsed_args
    input_file = urlopen(PLUGINS_XML_URL)
    dom_root = parse(input_file)
    input_file.close()

    plugins = plugins_dom_to_std_objs(dom_root)
    recent_plugins = list(filter_for_plugins_in_n_days(plugins, n_days))
    if not recent_plugins:
        return
    recent_plugins.sort(key=lambda p: p['release_date'], reverse=True)

    msg = '\n'.join((fmt_plugin(plugin) for plugin in recent_plugins))
    if email_to:
        email_msg(email_to, msg, 'Updates to plugins.xml')
    else:
        print msg

main(sys.argv[1:])
