import sys
import re
import itertools

FILE_SIZE_RE = re.compile(r'(\d+)mb')
REPEAT_STRING = 'fu skript kiddiez '
def main(args):
  if len(args) < 1:
    print 'Specify a file size in megabytes, e.g.: 10mb'
    return
  m = FILE_SIZE_RE.match(args[0])
  if not m:
    print 'File size must be something like: 10mb'
    return
  size_mb = m.group(1)
  size_b = 1024 * 1024 * int(size_mb)
  repeatn = 1 + size_b / len(REPEAT_STRING)
  for _ in itertools.repeat(None, repeatn):
    sys.stdout.write(REPEAT_STRING)

main(sys.argv[1:])
