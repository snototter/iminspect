#!/usr/bin/env python
# coding=utf-8
"""Utilities you'll often need when working with images ;-)"""

import numpy as np
import io
# import cv2
from PIL import Image


################################################################################
################################################################################
# Image I/O and basic conversion (grayscale, layer flipping, ...)

def imread(filename, mode='RGB', flip_channels=False):
    """Load an image (using PIL) into a NumPy array.

    Optionally specify PIL's loading 'mode', i.e. RGB for color, RGBA for a
    transparent image and L for grayscale. You can also flip the channels,
    i.e. convert RGB to BGR if you need it."""
    if filename is None:
        return None
    image = np.asarray(Image.open(filename).convert(mode))
    if flip_channels:
        return flip_layers(image)
    else:
        return image


# def imsave(filename, image, flip_channels=False):
#     """Store an image, taking care of flipping for you."""
#     if flip_channels:
#         cv2.imwrite(filename, flip_layers(image))
# # crappy JPEG presets, wtf!        Image.fromarray(flip_layers(image)).save(filename)
#     else:
#         cv2.imwrite(filename, image)


def ndarray2memory_file(np_data, format='png'):
    """Convert numpy (image) array to ByteIO stream. Useful to stream an image via sockets"""
    img = Image.fromarray(np_data)
    img_memory_file = io.BytesIO()
    img.save(img_memory_file, format)
    return img_memory_file


def memory_file2ndarray(memfile):
    """Load an image stored in the given io.BytesIO memory file memfile."""
    if memfile is None:
        return None
    return np.asarray(Image.open(memfile)) # TODO try with .frombuffer()


def flip_layers(nparray):
    """Flip RGB to BGR and vice versa, also accepts rgbA/bgrA and single channel images without crashing."""
    if len(nparray.shape) == 3:
        if nparray.shape[2] == 4:
            # We have xyzA, make zyxA
            return nparray[...,[2,1,0,3]]
        else:
            return nparray[:,:,::-1]
    return nparray


def clip_rect_to_image(rect, img_width, img_height):
    """Ensure that the rectangle is within the image boundaries, explicitly casts all entries to integer."""
    l, t, w, h = int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])
    w = w if (l + w) < img_width else (img_width - max(l, 0) - 1)
    h = h if (t + h) < img_height else (img_height - max(t, 0) - 1)
    l = l if l >= 0 else 0
    t = t if t >= 0 else 0
    return [l, t, w, h]


def is_valid_bbox(rect):
    """Left/top must be >= 0, W/H must be > 0"""
    return rect[0] >= 0 and rect[1] >= 0 and rect[2] > 0 and rect[3] > 0


def apply_on_bboxes(image_np, bboxes, func):
    """Applies the function func (which returns a modified image) on each bounding box.
    Takes care of proper clipping, roi extraction and copying back the results.
    """
    # Ensure the image is writeable
    image_np = image_np.copy()
    bboxes = [clip_rect_to_image(bb, image_np.shape[1], image_np.shape[0]) for bb in bboxes]
    bboxes = [b for b in bboxes if is_valid_bbox(b)]
    for bb in bboxes:
        l, t, w, h = bb
        roi = image_np[t:t+h, l:l+w]
        image_np[t:t+h, l:l+w] = func(roi)
    return image_np


def roi(image_np, rect):
    """Returns the cropped ROI, with rect = [l, t, w, h]."""
    if rect is None or any([r is None for r in rect]):
        return None # or return the full image, or raise a custom exception?
    l, t, w, h = rect
    r, b = l+w, t+h
    img_height, img_width = image_np.shape[0], image_np.shape[1]
    
    # Right/bottom bounds are exclusive; left/top are inclusive
    l = max(0, min(img_width-1, l))
    r = max(0, min(img_width, r))
    t = max(0, min(img_height-1, t))
    b = max(0, min(img_height, b))

    if len(image_np.shape) == 2:
        return image_np[t:b, l:r]
    return image_np[t:b, l:r, :]
