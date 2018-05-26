from urllib.request import urlopen
from io import BytesIO
from os.path import isfile
import subprocess

def pipInstallCmd(pkgname):
  print('    Suggested installation command: pip install', pkgname)

def testPackage(module, pipPkgName = None):
  if module:
    try:
      __import__(module)
      return True
    except ImportError:
      print('[ FAIL ] Could not import "%s"' % module)
      if pipPkgName: pipInstallCmd(pipPkgName)
      return False

def testVersion(module, expected_version, version, pipPkgName = None):
  satisfied = True
  for i in range(min(len(version), len(expected_version))):
    if version[i] != expected_version[i]:
      satisfied = False
      break
  if satisfied:
    print('[  ok  ] %s: %s' % (module, versionTupleToString(version)))
  else:
    print('[ FAIL ] %s: %s -- expected %s' % (module, versionTupleToString(version), versionTupleToString(expected_version)))
    if pipPkgName: pipInstallCmd(pipPkgName)
  return satisfied

def testPackageAndVersion(module, expected_version, version_func, pipPkgName):
  if testPackage(module, pipPkgName):
    return testVersion(module, expected_version, version_func(), pipPkgName)
  else:
    return False

def versionTupleToString(version):
  return '.'.join(map(str, version))

def intSafe(string):
  return int(string) if string.isdigit() else string

def versionStringToTuple(string):
  return tuple(map(intSafe, string.split('.')))

def testPython():
  from platform import python_version_tuple 
  testVersion("python", (3,6,2), python_version_tuple())

def getXapianVersion():
  import xapian
  return versionStringToTuple(xapian.version_string())

def getDjangoVersion():
  import django
  return django.VERSION

def getSocialAuthVersion():
  import social_auth
  return social_auth.version

def getMySQLdbVersion():
  import MySQLdb
  return MySQLdb.version_info

def getPILVersion():
  import PIL
  return versionStringToTuple(PIL.PILLOW_VERSION)

def testPILImageSupport(name, url):
  from PIL import Image

  try:
    f = BytesIO(urlopen(url).read())
    Image.open(f).load()
    print('[  ok  ] PIL supports', name)
  except:
    print('[ FAIL ] PIL could not load', name, 'file from', url)

def testMaven():
  import sys
  sys.path.append('.')
  from conf import mvn

  for var in ('MVN_BIN_PATH', 'MVN_SETTINGS_PATH'):
    path = getattr(mvn, var)
    if isfile(path):
      print('[  ok  ]', var, 'configured to:', path)
    else:
      print('[ FAIL ] Not configured correctly in conf.mvn:', var)
      return

  print( '   Testing Maven...')
  result = subprocess.call((mvn.MVN_BIN_PATH, '-version'))
  if result == 0:
    print( '[  ok  ] Invocation of Maven')

def testUnzip():
  result = subprocess.call(('unzip',))
  if result == 0:
    print('[  ok  ] Invocation of unzip')
  else:
    print( '[ FAIL ] Unable to invoke unzip')

def main():
  testPython()
  testPackageAndVersion("MySQLdb",       (1,),    getMySQLdbVersion,    'MySQL-Python==1.2.3')
  testPackageAndVersion("xapian",        (1,),    getXapianVersion,     None)
  if testPackageAndVersion("PIL",        (5,1,0), getPILVersion,        'Pillow==5.1.0'):
    testPILImageSupport('JPEG', 'http://upload.wikimedia.org/wikipedia/commons/3/38/JPEG_example_JPG_RIP_001.jpg')
    testPILImageSupport('PNG',  'http://upload.wikimedia.org/wikipedia/commons/8/89/PNG-Gradient.png')
    testPILImageSupport('GIF',  'http://upload.wikimedia.org/wikipedia/commons/a/a0/Sunflower_as_gif_websafe.gif')
  if testPackageAndVersion("django",     (2,0,5),   getDjangoVersion,     'Django==2.0.5'):
    testPackageAndVersion("social_auth", (0,7),   getSocialAuthVersion, 'django-social-auth==0.7.23')
  testMaven()
  testUnzip()

main()
