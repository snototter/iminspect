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
    # Visualize standard RGB image
    lena = imutils.imread('lena.jpg')
    inspect(lena, label='Demo RGB [{}]'.format(lena.dtype), initial_window_size=(400, 600))


    lena = imutils.imread('lena-alpha.png')
    inspect(lena, label='Demo RGBA [{}]'.format(lena.dtype))

    # Exemplary weight matrix
    weights = imutils.imread('peaks.png', mode='L')
    # Show as float data type, data range [-0.5, 0.5]
    weights_f32 = weights.astype(np.float32) / 255.0 - 0.5
    _, display_settings = inspect(weights_f32)

    # Inspect a boolean mask (and restore the previous display settings)
    mask = weights > 127
    _, display_settings = inspect(mask, display_settings=display_settings)

    # Inspect an image with 11 labels
    cats = (weights / 25).astype(np.int16) - 7
    _, display_settings = inspect(cats, data_type=DataType.CATEGORICAL, display_settings=display_settings)

    # Inspect a depth image
    depth = imutils.imread('depth.png')
    inspect(depth)

    # Inspect optical flow
    flow = flowutils.floread('color_wheel.flo')
    inspect(flow)

    # Another boolean mask
    mask = imutils.imread('space-invader.png', mode='L').astype(np.bool)
    inspect(mask)
