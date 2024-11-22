#!/usr/bin/env python
# coding=utf-8
import os
import math
import qimage2ndarray
from qtpy.QtCore import Qt
from qtpy.QtGui import QPainter, QFont, QColor, QPixmap, QImage, QPen, QIcon
from typing import Tuple
from pathlib import Path


# Utils to format a data point (depending on the range)
def fmtf(v):
    return '{:f}'.format(v)


def fmt4f(v):
    return '{:.4f}'.format(v)


def fmt3f(v):
    return '{:.3f}'.format(v)


def fmt2f(v):
    return '{:.2f}'.format(v)


def fmt1f(v):
    return '{:.1f}'.format(v)


def fmti(v):
    if not math.isfinite(v):
        return '?'  #TODO
    return '{:d}'.format(int(v))


def fmtb(v):
    return 'True' if v else 'False'


def bestFormatFx(limits):
    # Check range of data to select proper label formating
    span = limits[1] - limits[0]
    if span <= 0.5:
        return fmtf
    elif span <= 1.0:
        return fmt4f
    elif span <= 2.0:
        return fmt3f
    elif span < 10.0:
        return fmt2f
    elif span < 100.0:
        return fmt1f
    else:
        return fmti


def isArrayLike(v):
    """Checks if v is a tuple or list."""
    return isinstance(v, tuple) or isinstance(v, list)


def pixmapFromNumPy(img_np):
    if img_np.ndim < 3 or img_np.shape[2] in [1, 3, 4]:
        qimage = qimage2ndarray.array2qimage(img_np.copy())
    else:
        img_width = max(400, min(img_np.shape[1], 1200))
        img_height = max(200, min(img_np.shape[0], 1200))
        qimage = QImage(img_width, img_height, QImage.Format_RGB888)
        qimage.fill(Qt.white)
        qp = QPainter()
        qp.begin(qimage)
        qp.setRenderHint(QPainter.HighQualityAntialiasing)
        qp.setPen(QPen(QColor(200, 0, 0)))
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        font.setFamily('Helvetica')
        qp.setFont(font)
        qp.drawText(qimage.rect(), Qt.AlignCenter, "Error!\nCannot display a\n{:d}-channel image.".format(img_np.shape[2]))
        qp.end()
    if qimage.isNull():
        raise ValueError('Invalid image received, cannot convert it to QImage')
    return QPixmap.fromImage(qimage)


def emptyInspectionImage(img_size: Tuple[int, int] = (640, 320)):
    """Returns a dummy image to be displayed if the inspector is
    called with invalid (None) data."""
    img_width, img_height = img_size
    qimage = QImage(img_width, img_height, QImage.Format_RGB32)
    qimage.fill(Qt.white)
    qp = QPainter()
    qp.begin(qimage)
    qp.setRenderHint(QPainter.HighQualityAntialiasing)
    sz = min(100, min(img_width, img_height))
    logo = QIcon(str(Path(__file__).absolute().parent / 'iminspect_assets' / 'iminspect.svg')).pixmap(sz, sz)
    qp.drawPixmap((img_width - sz) // 2, 20, logo)
    qp.setPen(QPen(QColor(200, 0, 0)))
    font = QFont()
    font.setPointSize(24)
    font.setBold(True)
    font.setFamily('Helvetica')
    qp.setFont(font)
    qp.drawText(qimage.rect(), Qt.AlignCenter, "No data selected for inspection!")
    qp.end()
    return qimage2ndarray.rgb_view(qimage)
    # import numpy as np
    # npi = qimage2ndarray.rgb_view(qimage).astype(np.float32)
    # npi[0,0,0] = np.Inf
    # npi[10, 100, 2] = np.NaN
    # return npi

class FilenameUtils(object):
    @staticmethod
    def ensureFileExtension(filename, extensions):
        """Ensures that the given filename has one of the given extensions.
        Otherwise, the first element of extensions will be appended.
        :param filename: string
        :param extensions: list of strings
        """
        if filename is None:
            return None
        if len(filename) == 0:
            raise ValueError('Filename cannot be empty')
        if len(extensions) == 0:
            raise ValueError('List of extensions to test agains cannot be empty')
        _, ext = os.path.splitext(filename.lower())
        for e in extensions:
            # Ensure that the extension to test agains starts with '.'
            if e.startswith('.'):
                test_ext = e
            else:
                test_ext = '.' + e
            if test_ext.lower() == ext:
                return filename
        # No extension matched, thus append the first one
        if extensions[0].startswith('.'):
            return filename + extensions[0]
        else:
            return filename + '.' + extensions[0]

    @staticmethod
    def ensureImageExtension(filename):
        """Ensures that the given filename has an image type extension.
        Otherwise, appends PNG extension.
        """
        return FilenameUtils.ensureFileExtension(
            filename, ['.png', '.jpg', '.jpeg', '.ppm', '.bmp'])

    @staticmethod
    def ensureFlowExtension(filename):
        """Ensures that the given filename has the .flo extension."""
        return FilenameUtils.ensureFileExtension(
            filename, ['.flo'])

    @staticmethod
    def ensureNumpyExtension(filename):
        """Ensures that the given filename has the .npy extension."""
        return FilenameUtils.ensureFileExtension(
            filename, ['.npy'])
