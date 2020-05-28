import sys
from os import makedirs, rename
from os.path import basename, dirname, join as pathjoin, isdir, isfile
from django.core.management.base import BaseCommand
from django.conf import settings

fields = (
  # module        model         field           filepath-func
  ('apps.models', 'App',        'icon',         'app_icon_path'),
  ('apps.models', 'Release',    'release_file', 'release_file_path'),
  ('apps.models', 'Screenshot', 'screenshot',   'screenshot_path'),
  ('apps.models', 'Screenshot', 'thumbnail',    'thumbnail_path'),
  ('apps.models', 'ReleaseAPI', 'javadocs_jar_file', 'javadocs_path'),
  ('apps.models', 'ReleaseAPI', 'pom_xml_file', 'pom_xml_path'),
)

class Command(BaseCommand):
  def handle(self, *args, **options):
    for (module_name, model_name, field_name, func_name) in fields:
      module = __import__(module_name, fromlist=[''])
      model = getattr(module, model_name)
      func = getattr(module, func_name)
      for obj in model.objects.all():
        filefield = getattr(obj, field_name)
        if not filefield: continue

        filepath = filefield.name
        expectedpath = func(obj, basename(filepath))


        absfilepath = pathjoin(settings.MEDIA_ROOT, filepath)
        absexpectedpath = pathjoin(settings.MEDIA_ROOT, expectedpath)
        expecteddirpath = dirname(absexpectedpath)

        if absfilepath == absexpectedpath and isfile(absexpectedpath): continue

        if not isdir(expecteddirpath):
          sys.stdout.write('mkdir ' + str(dirname(absexpectedpath)) + '\n')
          makedirs(dirname(absexpectedpath))

        if isfile(absfilepath):
          sys.stdout.write('mv ' + str(absfilepath) + ' ' + str(absexpectedpath) + '\n')
          rename(absfilepath, absexpectedpath)
        elif isfile(absexpectedpath):
          sys.stdout.write(str(model_name) + '.' + str(obj.id) +
                           ': incorrect path in db; ok\n')
        else:
          sys.stdout.write('MISSING FILE! (' + str(model_name) + '.' +
                           str(obj.id) + ') ' + str(absfilepath) + '\n')

        filefield.name = expectedpath
        obj.save()
