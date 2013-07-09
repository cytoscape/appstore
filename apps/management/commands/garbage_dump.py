import os
import os.path
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.models import App, Release, ReleaseAPI, Screenshot, Tag, Author
from submit_app.models import AppPending

def rm_empty_tags():
	for tag in Tag.objects.all():
		if not App.objects.filter(tags = tag).count():
			tag.delete()
			yield tag.name

def rm_empty_authors():
	for author in Author.objects.all():
		if not App.objects.filter(authors = author).count():
			author.delete()
			yield str(author)

FILE_FIELDS = (
	(Screenshot, 'screenshot'),
	(Screenshot, 'thumbnail'),
	(Release,    'release_file'),
	(ReleaseAPI, 'javadocs_jar_file'),
	(ReleaseAPI, 'pom_xml_file'),
	(AppPending, 'release_file'),
	(App,        'icon'),
)

def add_files_to_set(s, dirname, names):
    for name in names:
        path = os.path.join(dirname, name) 
        if os.path.isfile(path):
            abspath = os.path.abspath(path)
            s.add(unicode(abspath))

def get_all_media_files():
	all_files = set()
	os.path.walk(settings.MEDIA_ROOT, add_files_to_set, all_files)
	return all_files

def get_used_media_files():
    used_files = set()
    for model, field_name in FILE_FIELDS:
        for obj in model.objects.all():
            field = getattr(obj, field_name)
            if not field: continue
            abspath = os.path.abspath(field.path)
            used_files.add(unicode(abspath))
    return used_files

def rm_unused_media_files():
	all_files = get_all_media_files()
	used_files = get_used_media_files()
	unused_files = all_files - used_files
	for unused_file in unused_files:
		os.remove(unused_file)
		yield unused_file

class Command(BaseCommand):
	def handle(self, *args, **options):
		print 'Tag:'
		for tag in rm_empty_tags():
			print '  ' + tag
		print

		print 'Author:'
		for author in rm_empty_authors():
			print '  ' + author
		print

    '''
		print 'Media:'
		for file_path in rm_unused_media_files():
			print '  ' + file_path
    '''
