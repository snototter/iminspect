#!/usr/bin/env python
# coding=utf-8
"""
Showcasing image viewer capabilities.
"""

import os
import sys

# Extend the python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from iminspect import imgview

if __name__ == "__main__":
    imgview.run_demo()
