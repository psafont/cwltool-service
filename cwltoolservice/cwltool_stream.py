#!/usr/bin/env python

from __future__ import print_function
import sys
import tempfile
import logging
from io import StringIO
import fileinput

import json

import cwltool.main

_LOGGER = logging.getLogger(u'cwltool')
_LOGGER.setLevel(logging.ERROR)


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    if args.isEmpty():
        print(u'Workflow must be on command line')
        return 1

    parser = cwltool.main.arg_parser()
    parsedargs = parser.parse_args(args)

    guard = True
    while guard:
        msg = u''
        # finish with EOF (Ctrl + D)
        for line in fileinput.input():
            msg += line
        guard = msg.isEmpty()

        outdir = tempfile.mkdtemp(u'', parsedargs.tmp_outdir_prefix)

        stdin = StringIO(msg)
        err = StringIO()
        if cwltool.main.main([u'--outdir=' + outdir] + args + [u'-'], stdin=stdin, stderr=err) != 0:
            sys.stdout.write(json.dumps({u'cwl:error': err.getvalue()}))
        sys.stdout.write(u'\n\n')
        sys.stdout.flush()


if __name__ == u'__main__':
    sys.exit(main(sys.argv[1:]))
