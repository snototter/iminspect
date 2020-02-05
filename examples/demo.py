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
    # If the user wants to load an image from disk:
    inspect(None)
    # Inspect a boolean mask
    mask = imutils.imread('space-invader.png', mode='L').astype(np.bool)
    inspect(mask)

    # Create exemplary label images
    cats1 = np.row_stack((np.arange(5), np.arange(5), np.arange(5), np.arange(5))).astype(np.int16)
    cats2 = np.row_stack((np.arange(5), np.arange(5), np.arange(5), np.arange(5))).astype(np.int16)
    cats2[2, :] = -42  # Category with an existing label (but non-sequential category value in contrast to the other categories)
    cats1[0, 1:-1] = 75 # Inject category without an existing label in both examples
    cats2[3, 1:-1] = 75
    labels = {0: 'car', 1: 'van', 2: 'truck', 3: 'bike', 4: 'person', 5: 'tree', -42: 'road'}

    print('You should scale these tiny images up, press Ctrl+F !!')
    inspect(
        (cats1, cats2),
        data_type=DataType.CATEGORICAL,
        categorical_labels=labels)

    # Exemplary weight matrix
    weights = imutils.imread('peaks.png', mode='L')
    # Show as float data type, data range [-0.5, 0.5]
    weights_f32 = weights.astype(np.float32) / 255.0 - 0.5
    _, display_settings = inspect(weights_f32)

    # Inspect an image with 11 labels.
    cats = (weights / 25).astype(np.int16) - 5
    _, display_settings = inspect(
        cats,
        data_type=DataType.CATEGORICAL)

    # Inspect a depth image
    depth = imutils.imread('depth.png')
    inspect(depth)

    # Inspect optical flow
    flow = flowutils.floread('color_wheel.flo')
    inspect(flow)

    # Visualize standard RGB image
    rgb = imutils.imread('flamingo.jpg')
    inspect(rgb, label='Demo RGB [{}]'.format(rgb.dtype))

    # # Inspect RGBA image
    # rgb = imutils.imread('flamingo-alpha.png')
    # inspect(rgb, label='Demo RGBA [{}]'.format(rgb.dtype))
