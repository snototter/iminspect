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
from iminspect.inspector import inspect


def imread(filename, mode='RGB'):
    """Load an image (using PIL) into a NumPy array."""
    return np.asarray(Image.open(filename).convert(mode))


if __name__ == "__main__":
    # Visualize standard RGB image
    lena = imread('lena.jpg', mode='RGB')
    inspect(lena, label='Demo RGB [{}]'.format(lena.dtype))

    # Exemplary weight matrix
    weights = imread('peaks.png', mode='L')
    # Show as float data type, data range [-0.5, 0.5]
    weights_f32 = weights.astype(np.float32) / 255.0 - 0.5
    inspect(weights_f32, label='Demo monochrome [{}]'.format(weights_f32.dtype))

    # Inspect a boolean mask
    mask = weights > 127
    inspect(mask, label='Demo mask [{}]'.format(mask.dtype))

    # # Inspect an integer label image
    # lbls = np.zeros(mask.shape, dtype=np.int16)
    # lbls[weights < 20] = 3
    # lbls[mask] = -23
    # inspector.inspect(lbls, label='Demo labels [{}]'.format(lbls.dtype), is_categoric=True)

    # # Inspect an image with 256 labels
    # inspector.inspect(weights, is_categoric=True, label='Demo 256 labels')

    # Inspect an image with 11 labels
    cats = (weights / 25).astype(np.int16) - 7
    inspect(cats, is_categoric=True, label='Demo 11 labels')




