#!/usr/bin/env python
# coding=utf-8
"""Showcasing data inspection"""

import os
import sys

from PIL import Image
import numpy as np

# Extend the python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import iminspect.utils as utils
import iminspect.inspector as inspector


if __name__ == "__main__":
    # Test RGB image
    lena = utils.imread('lena.jpg', mode='RGB')
    inspector.inspect(lena, flip_channels=False, label='Demo RGB [{}]'.format(lena.dtype))

    # Exemplary weight matrix
    weights = utils.imread('peaks.png', mode='L')
    # Show as float data type
    weights_f32 = weights.astype(np.float32) / 255.0 - 0.5
    inspector.inspect(weights_f32, label='Demo [{}]'.format(weights_f32.dtype))

    # Inspect a boolean mask
    mask = weights > 127
    inspector.inspect(mask, label='Demo [{}]'.format(mask.dtype))

    # Inspect an integer label image
    lbls = np.zeros(mask.shape, dtype=np.int16)
    lbls[weights < 20] = 3
    lbls[mask] = -23
    inspector.inspect(lbls, label='Label demo [{}]'.format(lbls.dtype), is_categoric=True)

    # Inspect an image with many labels
    inspector.inspect(weights, is_categoric=True, label='Monochrome input as categoric data')
    cats = (weights / 25).astype(np.int16) - 7
    inspector.inspect(cats, is_categoric=True, label='Monochrome input to 11-categories')




