#!/usr/bin/env python
# coding=utf-8
"""
A Qt-based image viewer which supports zooming and scrolling.
"""

from enum import Enum
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QScrollArea,\
    QHBoxLayout, QVBoxLayout, QDialog
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QSize, QPointF, QPoint, QRect
from PyQt5.QtGui import QPainter, QPixmap, QCursor, QBrush, QColor, QPen
import qimage2ndarray


class ImageCanvas(QWidget):
    """Widget to display an image."""

    zoomRequest = pyqtSignal(int)
    scrollRequest = pyqtSignal(int, int)
    mouseMoved = pyqtSignal(QPointF)
    rectSelected = pyqtSignal(tuple)

    def __init__(
            self, parent=None, rect_selectable=False,
            overlay_rect_color=QColor(200, 0, 0, 255), overlay_rect_fill_opacity=0,
            overlay_brush_color=QColor(128, 128, 200, 180)):
        super(ImageCanvas, self).__init__(parent)
        self._scale = 1.0
        self._pixmap = QPixmap()
        self._painter = QPainter()
        self._is_rect_selectable = rect_selectable
        self._prev_pos = None
        self._overlay_rect_color = overlay_rect_color
        self._overlay_rect_fill_opacity = overlay_rect_fill_opacity
        self._overlay_brush_color = overlay_brush_color
        self._rectangle = None
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
        if self._is_rect_selectable and Qt.LeftButton & event.buttons():
            # Skip mouse move signals during rect selection
            if self._prev_pos is None:
                self._prev_pos = pos
            else:
                x = [int(v) for v in [pos.x(), self._prev_pos.x()]]
                y = [max(0, min(self._pixmap.height()-1, int(v))) for v in [pos.y(), self._prev_pos.y()]]
                l, r = min(x), max(x)
                t, b = min(y), max(y)
                w = r - l
                h = b - t
                self.setRectangle((l, t, w, h))
        else:
            self.mouseMoved.emit(pos)

    def mousePressEvent(self, event):
        if self._is_rect_selectable and Qt.LeftButton == event.button():
            self._prev_pos = self.transformPos(event.pos())
            self._rectangle = None

    def mouseReleaseEvent(self, event):
        if self._is_rect_selectable and Qt.LeftButton == event.button() and self._rectangle is not None:
            self.rectSelected.emit(self._rectangle)

    def paintEvent(self, event):
        if not self._pixmap:
            return super(ImageCanvas, self).paintEvent(event)
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
            exposed_rect = inv_wt.mapRect(event.rect()).adjusted(-1, -1, 1, 1)
            qp.drawPixmap(exposed_rect, self._pixmap, exposed_rect)
        else:
            qp.translate(self.offsetToCenter())
            qp.drawPixmap(0, 0, self._pixmap)
            exposed_rect = QRect(0, 0, self._pixmap.width(), self._pixmap.height())

        # Draw overlays
        if self._is_rect_selectable and self._rectangle is not None:
            l, t, w_roi, h_roi = self._rectangle
            r = l + w_roi
            b = t + h_roi

            brush = QBrush(self._overlay_brush_color)
            # View/drawable area
            vx, vy = 0, 0
            vw = self._pixmap.width()
            vh = self._pixmap.height()

            # Fill top
            h = t-vy
            if h > 0:
                qp.fillRect(QRect(vx, vy, vw, h), brush)
            # Fill left
            w = l - vx
            if w > 0:
                qp.fillRect(QRect(vx, t, w, h_roi), brush)
            # Fill right
            w = vx + vw - r
            if w > 0:
                qp.fillRect(QRect(r, t, w, h_roi), brush)
            # # Fill bottom
            h = vy + vh - b
            if h > 0:
                qp.fillRect(QRect(vx, b, vw, h), brush)
            # Draw rectangle
            if self._overlay_rect_fill_opacity > 0:
                color = self._overlay_rect_color
                color.setAlpha(self._overlay_rect_fill_opacity)
                qp.fillRect(QRect(l, t, w_roi, h_roi), QBrush(color))
            qp.setPen(QPen(self._overlay_rect_color, 3, Qt.SolidLine))
            qp.drawLine(QPoint(l, t), QPoint(r, t))
            qp.drawLine(QPoint(r, t), QPoint(r, b))
            qp.drawLine(QPoint(r, b), QPoint(l, b))
            qp.drawLine(QPoint(l, b), QPoint(l, t))
        qp.end()

    def setRectangle(self, rect):
        if self._pixmap is None:
            return
        # Sanity check the given rect
        l, t, w, h = rect
        r = l + w
        b = t + h
        li = max(0, min(self._pixmap.width()-1, int(l)))
        ri = max(0, min(self._pixmap.width()-1, int(r)))
        ti = max(0, min(self._pixmap.height()-1, int(t)))
        bi = max(0, min(self._pixmap.height()-1, int(b)))
        wi = ri - li
        hi = bi - ti
        self._rectangle = (li, ti, wi, hi)
        self.update()

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
        area = super(ImageCanvas, self).size()
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
        return super(ImageCanvas, self).minimumSizeHint()

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


class ImageViewerType(Enum):
    """Enumeration for image viewers."""
    VIEW_ONLY = 1       # Just show the image
    RECT_SELECTION = 2  # Let user select a rectangle


class ImageViewer(QScrollArea):
    mouseMoved = pyqtSignal(QPointF)
    rectSelected = pyqtSignal(tuple)

    def __init__(self, parent=None, viewer_type=ImageViewerType.VIEW_ONLY, **kwargs):
        super(ImageViewer, self).__init__(parent)
        self._img_np = None
        self._img_scale = 1.0
        self._min_img_scale = None
        self._linked_viewers = list()
        self._viewer_type = viewer_type
        self._prepareLayout(**kwargs)

    @pyqtSlot(tuple)
    def _emitRectSelected(self, rect):
        self.rectSelected.emit(rect)

    def setRectangle(self, rect):
        self._canvas.setRectangle(rect)

    def _prepareLayout(self, **kwargs):
        if self._viewer_type == ImageViewerType.VIEW_ONLY:
            self._canvas = ImageCanvas(self)
        elif self._viewer_type == ImageViewerType.RECT_SELECTION:
            self._canvas = ImageCanvas(self, rect_selectable=True, **kwargs)
        else:
            raise RuntimeError('Unsupported ImageViewerType')
        self._canvas.rectSelected.connect(self._emitRectSelected)

        self._canvas.zoomRequest.connect(self.zoom)
        self._canvas.scrollRequest.connect(self.scroll)
        self._canvas.mouseMoved.connect(self.mouseMovedHandler)

        self.setWidget(self._canvas)
        self.setWidgetResizable(True)
        self._scoll_bars = {
            Qt.Vertical: self.verticalScrollBar(),
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
                QApplication.instance().processEvents()
                bar.setValue(bval)

    def currentImageScale(self):
        """Returns the currently applied image scale factor."""
        return self._img_scale

    @pyqtSlot(QPointF)
    def mouseMovedHandler(self, pixmap_pos):
        self.mouseMoved.emit(pixmap_pos)

    @pyqtSlot(int, int)
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

    @pyqtSlot(int)
    def zoom(self, delta, notify_linked=True):
        """Scale the displayed image. Zoom in if delta > 0.
        Usually to be called with mouse wheel delta values, thus
        the actual zoom steps are computed as delta/120.
        """
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
            self.scroll(delta_widget.x()*120/self.horizontalScrollBar().singleStep(), Qt.Horizontal, notify_linked=True)
            self.scroll(delta_widget.y()*120/self.verticalScrollBar().singleStep(), Qt.Vertical, notify_linked=True)
        # TODO emit mouse moved if cursor hovers over the image (pixel position may have changed)

    @pyqtSlot(int, int)
    def scroll(self, delta, orientation, notify_linked=True):
        """Slot for scrollRequest signal of image canvas."""
        steps = -delta / 120
        bar = self._scoll_bars[orientation]
        bar.setValue(bar.value() + bar.singleStep() * steps)
        if notify_linked:
            for v in self._linked_viewers:
                v.scroll(delta, orientation, notify_linked=False)
        # TODO emit mouse moved if cursor hovers over the image (pixel position may have changed)

    def showImage(self, img, adjust_size=True):
        qimage = qimage2ndarray.array2qimage(img.copy())
        if qimage.isNull():
            raise ValueError('Invalid image received, cannot convert it to QImage')
        self._img_np = img.copy()
        self._canvas.loadPixmap(QPixmap.fromImage(qimage))

        # Ensure that image has a minimum size of about 32x32 px (unless it is
        # actually smaller)
        self._min_img_scale = min(1.0, 32.0/img.shape[0], 32.0/img.shape[1])

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
        eps = 2.0  # Prevent scrollbars
        w1 = self.width() - eps
        h1 = self.height() - eps
        a1 = w1 / h1
        w2 = float(self._canvas.pixmap().width())
        h2 = float(self._canvas.pixmap().height())
        a2 = w2 / h2
        self._img_scale = w1 / w2 if a2 >= a1 else h1 / h2
        self.paintCanvas()
        # TODO emit mouse moved if cursor hovers over the image (pixel position may have changed)

    def setScale(self, scale):
        self._img_scale = scale
        self.paintCanvas()

    def paintCanvas(self):
        if self._img_np is None:
            return
        self._img_scale = max(self._min_img_scale, self._img_scale)
        self._canvas.setScale(self._img_scale)
        self._canvas.adjustSize()
        self._canvas.update()


class RectSelectionDialog(QDialog):
    rectSelected = pyqtSignal(object)

    def __init__(self, parent=None):
        super(RectSelectionDialog, self).__init__()
        layout = QVBoxLayout()
        self._img_viewer = ImageViewer(viewer_type=ImageViewerType.RECT_SELECTION)
        self._img_viewer.rectSelected.connect(self._emitRectSelected)
        layout.addWidget(self._img_viewer)
        self.setLayout(layout)

    def _emitRectSelected(self, rect):
        self.rectSelected.emit(rect)

    def showImage(self, img_np):
        self._img_viewer.showImage(img_np)

    def setRectangle(self, rect_img_coords):
        self._img_viewer.setRectangle(rect_img_coords)


class ImageViewerDemoApplication(QMainWindow):
    """Demo GUI showing three linked image
    viewers next to each other."""
    def __init__(self):
        super(ImageViewerDemoApplication, self).__init__()
        self._prepareLayout()

    def _prepareLayout(self):
        import sys
        sys.path.append('..')
        from iminspect.inputs import VLine
        self._main_widget = QWidget()
        main_layout = QHBoxLayout()

        img_viewer_a = ImageViewer(viewer_type=ImageViewerType.RECT_SELECTION)
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
    import os
    import sys
    img_np = np.asarray(Image.open(
        os.path.join(os.path.dirname(
            os.path.abspath(__file__)), '../examples/lena.jpg')).convert('RGB'))
    main_window = ImageViewerDemoApplication()
    main_window.show()
    main_window.showImage(img_np)
    sys.exit(app.exec_())


if __name__ == '__main__':
    run_demo()
