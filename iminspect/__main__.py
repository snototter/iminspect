#!/usr/bin/env python
# coding=utf-8
"""
Main utility to start iminspect like a "standalone" application.

For convenience, you should create a launcher to execute:
path/to/venv/.../python -m iminspect

See https://stackoverflow.com/questions/14132789/relative-imports-for-the-billionth-time
why running a script from this package via (path/to/script.py) won't work.
"""


from . import inspector
import argparse
from pathlib import Path
from vito import imutils


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Inspect an images or multiple images')
    parser.add_argument(
        'image', nargs='*', type=Path, help='Image file(s) to inspect', default=None)
    
    args = parser.parse_args()
    if args.image is None:
        to_inspect = None
    else:
        to_inspect = [imutils.imread(img) for img in args.image]
    
    inspector.inspect(data=to_inspect)
