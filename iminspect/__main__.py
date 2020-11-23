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

if __name__ == '__main__':
    inspector.inspect(None)