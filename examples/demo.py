#!/usr/bin/env python
# coding=utf-8
"""
Showcasing data inspection

This example script needs PIL (Pillow package) to load images from disk.
"""

import os
import sys

import numpy as np

# Extend the python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from iminspect.inspector import inspect, DataType

from vito import imutils
from vito import flowutils

if __name__ == "__main__":
    # Inspect a boolean mask
    mask = imutils.imread('space-invader.png', mode='L').astype(np.bool)
    inspect(mask)

    # Exemplary weight matrix
    weights = imutils.imread('peaks.png', mode='L')
    # Show as float data type, data range [-0.5, 0.5]
    weights_f32 = weights.astype(np.float32) / 255.0 - 0.5
    _, display_settings = inspect(weights_f32)

    # Inspect an image with 11 labels, restore the previous UI settings
    cats = (weights / 25).astype(np.int16) - 7
    _, display_settings = inspect(
        cats,
        data_type=DataType.CATEGORICAL,
        display_settings=display_settings)

    # Inspect a depth image
    depth = imutils.imread('depth.png')
    inspect(depth)

    # Inspect optical flow
    flow = flowutils.floread('color_wheel.flo')
    inspect(flow)

    # Visualize standard RGB image
    lena = imutils.imread('lena.jpg')
    inspect(lena, label='Demo RGB [{}]'.format(lena.dtype))

    # # Inspect RGBA image
    # lena = imutils.imread('lena-alpha.png')
    # inspect(lena, label='Demo RGBA [{}]'.format(lena.dtype))
