#!/usr/bin/env python3
#PBS -q isi
#PBS -l walltime=1:00:00

# code by Jon May [jonmay@isi.edu]
import argparse
import sys
import codecs
if sys.version_info[0] == 2:
  from itertools import izip
else:
  izip = zip
from collections import defaultdict as dd
import re
import os.path
import gzip
import tempfile
import shutil
import atexit
scriptdir = os.path.dirname(os.path.abspath(__file__))

reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')


def prepfile(fh, code):
  ret = gzip.open(fh.name, code) if fh.name.endswith(".gz") else fh
  if sys.version_info[0] == 2:
    if code.startswith('r'):
      ret = reader(fh)
    elif code.startswith('w'):
      ret = writer(fh)
    else:
      sys.stderr.write("I didn't understand code "+code+"\n")
      sys.exit(1)
  return ret

def main():
  parser = argparse.ArgumentParser(description="given data from nmt rescoring, convert it to something appropriate for appending to sbmt nbest files",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infiles", "-i", nargs='+', type=argparse.FileType('r'), default=[sys.stdin,], help="input files; each is whitespace-separated log prob; all must have same number of lines")
  parser.add_argument("--amendfile", "-a", type=argparse.FileType('r'), default=[sys.stdin,], help="original nbest file; should match in number of lines to infiles")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file; space-separated feat=val where val is negative log prob")
  parser.add_argument("--prefix", "-p", type=str, default='nmt', help='prefix for name of features')

  workdir = tempfile.mkdtemp(prefix=os.path.basename(__file__), dir=os.getenv('TMPDIR', '/tmp'))

  def cleanwork():
    shutil.rmtree(workdir, ignore_errors=True)
  atexit.register(cleanwork)


  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infiles = []
  for ifh in args.infiles:
    infiles.append(prepfile(ifh, 'r'))
  amendfile = prepfile(args.amendfile, 'r')

  outfile = prepfile(args.outfile, 'w')

  tuplen = -1
  featurenames = []
  for ln, tup in enumerate(izip(amendfile, *infiles), start=1):
    vals = []
    prev = tup[0]
    for line in tup[1:]:
      for val in line.strip().split():
        featname = "%s_%d" % (args.prefix, len(vals)) 
        if tuplen == -1:
          featurenames.append(featname)
        vals.append("%s=%f" % (featname, -(float(val))))
    if tuplen == -1:
      tuplen = len(vals)
    elif len(vals) != tuplen:
      sys.stderr.write("Expected all lines to have %d items but got %d at line %d\n" % (tuplen, len(vals), ln))
      sys.exit(1)
    outfile.write(prev.strip()+" "+' '.join(vals)+"\n")
  sys.stdout.write(' '.join(featurenames)+"\n")
if __name__ == '__main__':
  main()
