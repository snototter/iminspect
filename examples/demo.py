#!/usr/bin/env python
# coding=utf-8
"""
Showcasing data inspection

This example script needs PIL (Pillow package) to load images from disk.
"""

import os
import sys

from PIL import Image
import numpy as np

# Extend the python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from iminspect.inspector import inspect, DataType

from vito import imutils
from vito import flow

if __name__ == "__main__":
    # Visualize standard RGB image
    # lena = imutils.imread('lena.jpg')
    # inspect(lena, label='Demo RGB [{}]'.format(lena.dtype))

    # # Exemplary weight matrix
    # weights = imutils.imread('peaks.png', mode='L')
    # # Show as float data type, data range [-0.5, 0.5]
    # weights_f32 = weights.astype(np.float32) / 255.0 - 0.5
    # _, display_settings = inspect(weights_f32, label='Demo monochrome [{}]'.format(weights_f32.dtype))

    # # Inspect a boolean mask (and restore the previous display settings)
    # mask = weights > 127
    # _, display_settings = inspect(mask, label='Demo mask [{}]'.format(mask.dtype), display_settings=display_settings)

    # # # Inspect an integer label image
    # # lbls = np.zeros(mask.shape, dtype=np.int16)
    # # lbls[weights < 20] = 3
    # # lbls[mask] = -23
    # # inspector.inspect(lbls, label='Demo labels [{}]'.format(lbls.dtype), is_categoric=True)

    # # # Inspect an image with 256 labels
    # # inspector.inspect(weights, is_categoric=True, label='Demo 256 labels')

    # # Inspect an image with 11 labels
    # cats = (weights / 25).astype(np.int16) - 7
    # _, display_settings = inspect(cats, data_type=DataType.CATEGORIC, label='Inspect image with 11 labels', display_settings=display_settings)

    # # Inspect a depth image
    # depth = imutils.imread('depth.png')
    # inspect(depth, label='Depth Image')
    
    # Inspect optical flow
    f = flow.floread('color_wheel.flo')
    inspect(f, label='Optical Flow')
