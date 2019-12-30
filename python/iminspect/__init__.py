#!/usr/bin/env python
# coding=utf-8
"""
Python Qt5 utils to easily visualize image data for faster development.
"""

__all__ = ['colormaps', 'imgview', 'inputs', 'inspector']
__author__ = 'snototter'

# Load version
import os
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'version.py')) as vf:
    exec(vf.read())
