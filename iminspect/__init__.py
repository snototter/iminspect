#!/usr/bin/env python
# coding=utf-8
"""
Python Qt5 utils to easily visualize image data for faster development.
"""

__all__ = ['imgview', 'inputs', 'inspection_utils', 'inspection_widgets', 'inspector']
__author__ = 'snototter'

# Load version
import os
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'version.py')) as vf:
    exec(vf.read())


def show(data, **kwargs):
    """Just a "symlink" to iminspector.inspector.inspect() for convenience/out
    of laziness. Refer to inspector.inspect() for the actual documentation.

    How to save a few characters using this wrapper:
    import numpy as np
    import iminspect
    iminspect.show(np.random.rand(16, 16))
    """
    from . import inspector
    inspector.inspect(data, **kwargs)
