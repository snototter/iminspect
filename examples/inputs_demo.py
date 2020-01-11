#!/usr/bin/env python
# coding=utf-8
"""
Showcasing custom input widgets.
"""

import os
import sys

# Extend the python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from iminspect import inputs

if __name__ == "__main__":
    inputs.run_demo()
