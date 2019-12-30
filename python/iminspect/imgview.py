#!/usr/bin/env python
# coding=utf-8
"""
A Qt-based image viewer which supports zooming and scrolling.
""" 

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import qimage2ndarray

class ImageCanvas(QWidget):
    """Widget to display an image."""

    zoomRequest = pyqtSignal(int)
    scrollRequest = pyqtSignal(int, int)
    mouseMoved = pyqtSignal(QPointF)

    def __init__(self, *args, **kwargs):
        super(type(self), self).__init__(*args, **kwargs)
        self._scale = 1.0
        self._pixmap = QPixmap()
        self._painter = QPainter()
        self.setMouseTracking(True)

    def setScale(self, scale):
        self._scale = scale
        self.adjustSize()
        self.update()

    def loadPixmap(self, pixmap):
        self._pixmap = pixmap
        self.repaint()

    def pixmap(self):
        return self._pixmap

    def mouseMoveEvent(self, event):
        pos = self.transformPos(event.pos())
        self.mouseMoved.emit(pos)

    def paintEvent(self, event):
        if not self._pixmap:
            return super(type(self), self).paintEvent(event)
        qp = self._painter
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing)
        qp.setRenderHint(QPainter.HighQualityAntialiasing)
        # qp.setRenderHint(QPainter.SmoothPixmapTransform)
        qp.scale(self._scale, self._scale)
        # Adapted fast drawing from: 
        # https://www.qt.io/blog/2006/05/13/fast-transformed-pixmapimage-drawing
        # If the painter has an invertible world transformation matrix, we use
        # it to get the visible rectangle (saves a lot of drawing resources).
        inv_wt, valid = qp.worldTransform().inverted()
        if valid:
            qp.translate(self.offsetToCenter())
            exposed = inv_wt.mapRect(event.rect()).adjusted(-1, -1, 1, 1)
            qp.drawPixmap(exposed, self._pixmap, exposed)
        else:
            qp.translate(self.offsetToCenter())
            qp.drawPixmap(0, 0, self._pixmap)
        qp.end()

    def transformPos(self, point):
        """Convert from widget coordinates to painter coordinates."""
        return QPointF(point.x()/self._scale, point.y()/self._scale) - self.offsetToCenter()

    def pixelAtWidgetPos(self, widget_pos):
        """Returns the pixel position at the given widget coordinate."""
        return self.transformPos(widget_pos)

    def pixelToWidgetPos(self, pixel_pos):
        """Compute the widget position of the given pixel position."""
        return (pixel_pos + self.offsetToCenter()) * self._scale

    def offsetToCenter(self):
        area = super(type(self), self).size()
        aw, ah = area.width(), area.height()
        w = self._pixmap.width() * self._scale
        h = self._pixmap.height() * self._scale
        x = (aw - w) / (2 * self._scale) if aw > w else 0
        y = (ah - h) / (2 * self._scale) if ah > h else 0
        return QPointF(x, y)

    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        if self._pixmap:
            return self._scale * self._pixmap.size()
        return super(type(self), self).minimumSizeHint()

    def wheelEvent(self, event):
        delta = event.angleDelta()
        dx, dy = delta.x(), delta.y()
        modifiers = event.modifiers()
        if modifiers & Qt.ControlModifier:
            if modifiers & Qt.ShiftModifier:
                dy *= 10
            if dy:
                self.zoomRequest.emit(dy)
        else:
            if modifiers & Qt.ShiftModifier:
                dx *= 10
                dy *= 10
            dx and self.scrollRequest.emit(dx, Qt.Horizontal)
            dy and self.scrollRequest.emit(dy, Qt.Vertical)
        event.accept()


class ImageViewer(QScrollArea):
    mouseMoved = pyqtSignal(QPointF)

    def __init__(self, parent=None):
        super(type(self), self).__init__(parent)
        self._img_np = None
        self._img_scale = 1.0
        self._min_img_scale = None
        self._linked_viewers = list()
        self._prepareLayout()
        
    def _prepareLayout(self):
        self._canvas = ImageCanvas(self)
        self._canvas.zoomRequest.connect(self.zoom)
        self._canvas.scrollRequest.connect(self.scroll)
        self._canvas.mouseMoved.connect(self.mouseMovedHandler)

        self.setWidget(self._canvas)
        self.setWidgetResizable(True)
        self._scoll_bars = { Qt.Vertical: self.verticalScrollBar(),
            Qt.Horizontal: self.horizontalScrollBar()
        }
        self.verticalScrollBar().sliderMoved.connect(lambda v: self.sliderChanged(v, Qt.Vertical))
        self.horizontalScrollBar().sliderMoved.connect(lambda v: self.sliderChanged(v, Qt.Horizontal))


    def currentDisplaySettings(self):
        """Query the current zoom/scroll settings, so you can restore them.
        For example, if you want to show the same region of interest for another
        image.
        """
        settings = {'zoom': self._img_scale}
        for orientation in [Qt.Horizontal, Qt.Vertical]:
            bar = self._scoll_bars[orientation]
            settings[orientation] = (bar.minimum(), bar.value(), bar.maximum())
        return settings

    def restoreDisplaySettings(self, settings):
        self._img_scale = settings['zoom']
        self.paintCanvas()
        # Potential issue: scrollbars may only appear during repainting the
        # widget. Then, setting their value won't work. Best and least 
        # complicated way I found so far: force Qt to process the event loop
        # after adjusting the bar's range (and before setting the new value).
        for orientation in [Qt.Horizontal, Qt.Vertical]:
            bar = self._scoll_bars[orientation]
            bmin, bval, bmax = settings[orientation]
            if bval != 0:
                bar.setMinimum(bmin)
                bar.setMaximum(bmax)
                qApp.processEvents()
                bar.setValue(bval)

    def currentImageScale(self):
        """Returns the currently applied image scale factor."""
        return self._img_scale

    def mouseMovedHandler(self, pixmap_pos):
        self.mouseMoved.emit(pixmap_pos)

    def sliderChanged(self, new_value, orientation):
        bar = self._scoll_bars[orientation]
        delta = new_value - bar.value()
        self.scroll(-delta * 120 / bar.singleStep(), orientation, notify_linked=True)

    def linkViewers(self, viewers):
        """'link_axes'-like behavior: link this ImageViewer to each
        ImageViewer in the given list such that they all zoom/scroll
        the same.
        """
        others = [v for v in viewers if v is not self]
        if others:
            self._linked_viewers.extend(others)

    def zoom(self, delta, notify_linked=True):
        # Currently, we adjust the scroll bar position such that the cursor stays 
        # at the same pixel. This works well if both scroll bars are visible, otherwise,
        # only one axes is adjusted accordingly.
        cursor_pos = QCursor().pos()
        px_pos_prev = self._canvas.pixelAtWidgetPos(self._canvas.mapFromGlobal(cursor_pos))
        self._img_scale += 0.05 * delta / 120
        self.paintCanvas()
        if notify_linked:
            # Zoom the linked viewers (if any)
            for v in self._linked_viewers:
                v.zoom(delta, notify_linked=False)
            # Adjust the scroll bar positions to keep cursor at the same pixel
            px_pos_curr = self._canvas.pixelAtWidgetPos(self._canvas.mapFromGlobal(cursor_pos))
            delta_widget = self._canvas.pixelToWidgetPos(px_pos_curr) - self._canvas.pixelToWidgetPos(px_pos_prev)
            self.scroll(delta_widget.x()*120/self.horizontalScrollBar().singleStep(), Qt.Horizontal, notify_linked=False)
            self.scroll(delta_widget.y()*120/self.verticalScrollBar().singleStep(), Qt.Vertical, notify_linked=False)

    def scroll(self, delta, orientation, notify_linked=True):
        """Slot for scrollRequest signal of image canvas."""
        steps = -delta / 120
        bar = self._scoll_bars[orientation]
        bar.setValue(bar.value() + bar.singleStep() * steps)
        if notify_linked:
            for v in self._linked_viewers:
                v.scroll(delta, orientation, notify_linked=False)

    def showImage(self, img, adjust_size=True):
        qimage = qimage2ndarray.array2qimage(img.copy())
        if qimage.isNull():
            raise ValueError('Invalid image received, cannot convert it to QImage')
        self._img_np = img.copy()
        self._canvas.loadPixmap(QPixmap.fromImage(qimage))

        # Ensure that image has a minimum size of about 32x32 px
        self._min_img_scale = min(32.0/img.shape[0], 32.0/img.shape[1])

        if self._img_np is None:
            self._canvas.setVisible(True)
            self._canvas.adjustSize()
        
        if adjust_size:
            # self._img_scale = 1.0
            self.scaleToFitWindow()
        self.paintCanvas()

    def scaleToFitWindow(self):
        """Scale the image such that it fills the canvas area."""
        if self._img_np is None:
            return
        eps = 2.0 # Prevent scrollbars
        w1 = self.width() - eps
        h1 = self.height() - eps
        a1 = w1 / h1
        w2 = float(self._canvas.pixmap().width())
        h2 = float(self._canvas.pixmap().height())
        a2 = w2 / h2
        self._img_scale = w1 / w2 if a2 >= a1 else h1 / h2
        self.paintCanvas()

    def paintCanvas(self):
        if self._img_np is None:
            return
        self._img_scale = max(self._min_img_scale, self._img_scale)
        self._canvas.setScale(self._img_scale)
        self._canvas.adjustSize()
        self._canvas.update()



class ImageViewerDemoApplication(QMainWindow):
    """Demo GUI showing three linked image 
    viewers next to each other."""
    def __init__(self, img_np):
        super(type(self), self).__init__()
        self._prepareLayout()
        self.show()
        self.showImage(img_np)

    def _prepareLayout(self):
        import sys
        sys.path.append('..')
        from iminspect.inputs import VLine
        self._main_widget = QWidget()
        main_layout = QHBoxLayout()

        img_viewer_a = ImageViewer()
        main_layout.addWidget(img_viewer_a)

        main_layout.addWidget(VLine())

        img_viewer_b = ImageViewer()
        main_layout.addWidget(img_viewer_b)

        main_layout.addWidget(VLine())

        img_viewer_c = ImageViewer()
        main_layout.addWidget(img_viewer_c)

        self._main_widget.setLayout(main_layout)
        self.setCentralWidget(self._main_widget)
        self.resize(QSize(1280, 300))

        # # Link all viewers, so they zoom/scroll the same...
        self._viewers = [img_viewer_a, img_viewer_b, img_viewer_c]
        for v in self._viewers:
            v.linkViewers(self._viewers)

    def showImage(self, img):
        for v in self._viewers:
            v.showImage(img)


def run_demo():
    app = QApplication(['Linked ImageViewer Demo'])
    import numpy as np
    from PIL import Image
    import os, sys
    img_np = image = np.asarray(Image.open(\
        os.path.join(os.path.dirname(\
            os.path.abspath(__file__)), '../examples/lena.jpg')).convert('RGB'))
    main_widget = ImageViewerDemoApplication(img_np)
    sys.exit(app.exec_())

if __name__ == '__main__':
    run_demo()