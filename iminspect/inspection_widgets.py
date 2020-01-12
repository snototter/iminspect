#!/usr/bin/env python
# coding=utf-8
"""Inspect matrix/image data"""

import math
import numpy as np
from PyQt5.QtWidgets import QWidget, QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QToolButton
from PyQt5.QtCore import Qt, QSize, QRect, QPoint, QPointF, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPainter, QFont, QFontMetrics, QBrush, QColor, QIcon, QPen

from vito import flowutils

from . import imgview
from . import inputs
from . import inspection_utils
from . import inspector


class ColorBar(QWidget):
    """Draws a vertical color bar."""
    def __init__(self):
        super(ColorBar, self).__init__()
        self._bar_width = 30
        self._bar_padding = 5
        self._min_height = 80
        self._font_size = 10
        self._num_labels = 10

        self.setMinimumHeight(self._min_height)
        self.setMinimumWidth(100)
        self._colormap = None
        self._limits = None
        self._show_flow_wheel = False
        self._is_boolean = False
        self._categories = None
        self._categorical_labels = None

    def setBoolean(self, b):
        # If the visualized data is boolean, set this to True!
        self._is_boolean = b

    def setCategories(self, c):
        # If the visualized data is categorical (i.e. a label image), set the unique categories!
        self._categories = c

    def setCategoricalLabels(self, lbl_dict):
        # If the data is categorical, you can provide a dict {category: 'some label'}
        self._categorical_labels = lbl_dict

    def setLimits(self, limits):
        self._limits = limits

    def setColormap(self, colormap):
        self._colormap = colormap

    def setFlowWheel(self, show_wheel):
        self._show_flow_wheel = show_wheel

    def paintEvent(self, event):
        if not self._show_flow_wheel and (self._colormap is None
                or (not self._is_boolean and self._categories is None and self._limits is None)):
            return
        size = self.size()
        qp = QPainter()
        qp.begin(self)
        font = QFont('sans-serif', self._font_size)
        font_metrics = QFontMetrics(font)
        qp.setFont(font)

        if self._is_boolean:
            # For binary/boolean data, we only need to show the two visualized colors.
            rgb = self._colormap[-1]
            brush = QBrush(QColor(rgb[0], rgb[1], rgb[2]))
            qp.fillRect(self._bar_padding, 0, self._bar_width, np.ceil(size.height()/2), brush)
            rgb = self._colormap[0]
            brush = QBrush(QColor(rgb[0], rgb[1], rgb[2]))
            qp.fillRect(self._bar_padding, np.floor(size.height()/2),
                        self._bar_width, np.ceil(size.height()/2), brush)
            # Draw labels
            qp.drawText(QPoint(2*self._bar_padding + self._bar_width, int(size.height()*0.25)),
                        'True')
            qp.drawText(QPoint(2*self._bar_padding + self._bar_width, int(size.height()*0.75)),
                        'False')
            max_label_width = font_metrics.width('False')
            self.setMinimumWidth(3 * self._bar_padding + self._bar_width + max_label_width)
        elif self._categories is not None:
            # For label images, we don't need the full colormap gradient, but only
            # one block for each class/label/category.

            # Compute height of each colored block.
            num_categories = len(self._categories)
            step_height = size.height() / float(num_categories)
            cm_indices = np.linspace(0, 255, num_categories).astype(np.uint8)
            # Draw the category colors from top to bottom (largest ID/category/label first).
            top = 0.0
            label_pos = list()
            for i in range(num_categories):
                rgb = self._colormap[cm_indices[num_categories-1-i]]
                brush = QBrush(QColor(rgb[0], rgb[1], rgb[2]))
                qp.fillRect(self._bar_padding, np.floor(top), self._bar_width, np.ceil(step_height), brush)
                # Compute label position (vertically centered, adjust if outside of canvas)
                ly = max(self._font_size, min(np.floor(top + step_height/2 + self._font_size/2), size.height()))
                label_pos.append(QPoint(2*self._bar_padding + self._bar_width, ly))
                # Move to next category.
                top += step_height
            # Now the label positions are computed from largest value to smallest, but
            # categories are listed from smallest value to largest. Thus:
            label_pos.reverse()
            # Draw labels (vertically centered on corresponding filled rects)
            # Check, if all labels fit (font size vs widget height).
            height_per_label = max(size.height() / num_categories, 1.1*self._font_size)
            num_labels = min(num_categories, int(math.ceil(size.height() / height_per_label)))
            # If there's too little space, select a subset of labels (and their
            # corresponding text positions).
            selected_idx = np.linspace(0, num_categories-1, num_labels)
            labels = [self._categories[int(i)] for i in selected_idx]
            lpos = [label_pos[int(i)] for i in selected_idx]
            longest_label = ''
            for i in range(num_labels):
                if self._categorical_labels is not None and labels[i] in self._categorical_labels:
                    txt = self._categorical_labels[labels[i]]
                else:
                    txt = inspection_utils.fmti(labels[i])
                if len(txt) > len(longest_label):
                    longest_label = txt
                qp.drawText(lpos[i], txt)
            max_label_width = font_metrics.width(longest_label)
            self.setMinimumWidth(3 * self._bar_padding + self._bar_width + max_label_width)
        elif self._show_flow_wheel:
            # Draw the flow color wheel, centered on the widget
            center = QPointF(size.width() / 2, size.height() / 2)
            diameter = int(min(size.width(), size.height()) - 2 * self._bar_padding)
            radius = diameter / 2
            # Create optical flow that will be visualized as color wheel
            coords = np.linspace(-1, 1, diameter)
            xv, yv = np.meshgrid(coords, coords)
            flow = np.dstack((xv, yv))
            colorized = flowutils.colorize_flow(flow)
            # Create an alpha mask to draw a circle
            alpha_mask = np.zeros((diameter, diameter), dtype=np.uint8)
            where = np.sqrt(np.square(xv) + np.square(yv)) <= 1.0
            alpha_mask[where] = 255
            colorized = np.dstack((colorized, alpha_mask))
            # Draw the color wheel
            qpixmap = inspection_utils.pixmapFromNumPy(colorized)
            qp.drawPixmap(center.x() - radius, center.y() - radius, qpixmap)
            # Overlay a cross
            cx, cy = center.x(), center.y()
            left, right = cx - radius, cx + radius
            top, bottom = cy - radius, cy + radius
            line_width = 1
            qp.setPen(QPen(Qt.black, line_width))
            qp.drawLine(cx, top + line_width, cx, bottom - line_width)
            qp.drawLine(left + line_width, cy, right - line_width, cy)
            # Label it
            txt_height = int((size.height() - 2*self._bar_padding - diameter - 5) / 2)
            if txt_height > 30:
                qp.drawText(QRect(center.x() - radius, self._bar_padding, diameter, txt_height),
                    Qt.AlignHCenter | Qt.AlignBottom, 'Flow\nColor Wheel')
            self.setMinimumWidth(2 * self._bar_padding + max(diameter, font_metrics.width('Color Wheel')))
        else:
            # Draw color gradients
            num_gradient_steps = min(size.height(), 256)
            step_height = size.height() / float(num_gradient_steps)
            cm_indices = np.linspace(0, 255, num_gradient_steps).astype(np.uint8)
            top = 0.0
            for i in range(num_gradient_steps):
                rgb = self._colormap[cm_indices[num_gradient_steps-1-i]]
                brush = QBrush(QColor(rgb[0], rgb[1], rgb[2]))
                qp.fillRect(self._bar_padding, np.floor(top),
                            self._bar_width, np.ceil(step_height), brush)
                top += step_height
            # Draw labels
            fmt = inspection_utils.bestFormatFx(self._limits)
            height_per_label = max(size.height() / self._num_labels, 2*self._font_size)
            num_labels = min(self._num_labels, int(size.height() / height_per_label))
            labels = np.linspace(self._limits[0], self._limits[1], num_labels)
            longest_label = ''
            for i in range(num_labels):
                pos = QPoint(2*self._bar_padding + self._bar_width,
                             int(size.height() - i * (size.height()-self._font_size)/(num_labels-1)))
                txt = fmt(labels[i])
                qp.drawText(pos, txt)
                if len(txt) > len(longest_label):
                    longest_label = txt
            max_label_width = font_metrics.width(longest_label)
            self.setMinimumWidth(3 * self._bar_padding + self._bar_width + max_label_width)
        # We're done painting
        qp.end()
        # Adjust widget's minimum width according to actual rendering


class OpenInspectionFileDialog(QDialog):
    def __init__(self, data_type=None, thumbnail=None, parent=None):
        """
        Dialog to open a file from disk.

        data_type:  None or inspector.DataType, is used to select the initial
                    file filter.
        thumbnail:  None or QPixmap, will be shown so the user knows which image
                    s/he is going to replace by the loaded file.
        """
        super(OpenInspectionFileDialog, self).__init__(parent)
        self._filename = None
        self._data_type = None
        self._confirmed = False
        self.__prepareLayout(data_type, thumbnail)

    def __prepareLayout(self, current_data_type, current_thumbnail):
        self.setWindowTitle('Open File')
        layout = QVBoxLayout()
        file_filters = 'Images (*.bmp *.jpg *.jpeg *.png *.ppm);;Optical Flow (*.flo);;NumPy Arrays (*.npy);;All Files (*.*)'
        if current_data_type is None:
            initial_filter = ''
        elif current_data_type == inspector.DataType.FLOW:
            initial_filter = 'Optical Flow (*.flo)'
        elif current_data_type == inspector.DataType.MULTICHANNEL:
            initial_filter = 'NumPy Arrays (*.npy)'
        else:
            initial_filter = ''
        self._file_widget = inputs.SelectDirEntryWidget('File:',
            inputs.SelectDirEntryType.FILENAME_OPEN, parent=self,
            filters=file_filters,
            initial_filter=initial_filter,
            min_label_width=None, relative_base_path=None)
        self._file_widget.value_changed.connect(self.__fileSelected)
        layout.addWidget(self._file_widget)

        self._type_widget = inputs.DropDownSelectionWidget('Type:',
            [(inspector.DataType.COLOR, 'Color'),
            (inspector.DataType.MONOCHROME, 'Monochrome'),
            (inspector.DataType.BOOL, 'Boolean Mask'),
            (inspector.DataType.CATEGORICAL, 'Categories / Labels'),
            (inspector.DataType.DEPTH, 'Depth'),
            (inspector.DataType.FLOW, 'Optical Flow'),
            (inspector.DataType.MULTICHANNEL, 'Multi-channel')])
        if current_data_type is not None:
            self._type_widget.set_value(current_data_type)
        layout.addWidget(self._type_widget)

        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton('Cancel')
        btn_cancel.clicked.connect(self.__onCancel)
        btn_layout.addWidget(btn_cancel)

        self._btn_confirm = QPushButton('Open')
        self._btn_confirm.clicked.connect(self.__onConfirm)
        self._btn_confirm.setEnabled(False)
        btn_layout.addWidget(self._btn_confirm)

        layout.addLayout(btn_layout)

        if current_thumbnail is None:
            self.setLayout(layout)
        else:
            # Show thumbnail left of input widgets, so the user knows which
            # viewer he is going to load the file into.
            thumb_layout = QVBoxLayout()
            thumb_layout.addWidget(QLabel('Currently shown:'))
            thumb_layout.addWidget(imgview.ImageLabel(current_thumbnail))
            hlayout = QHBoxLayout()
            hlayout.addLayout(thumb_layout)
            hlayout.addWidget(inputs.VLine())
            hlayout.addLayout(layout)
            self.setLayout(hlayout)

    def open(self):
        super(OpenInspectionFileDialog, self).open()
        self._file_widget.open_dialog()

    @pyqtSlot(object)
    def __fileSelected(self, filename):
        self._filename = filename
        if self._filename is not None and self._filename.lower().endswith('.flo'):
            self._type_widget.set_value(inspector.DataType.FLOW)
            self._type_widget.setEnabled(False)
        elif self._filename is not None and self._filename.lower().endswith('.npy'):
            self._type_widget.set_value(inspector.DataType.MULTICHANNEL)
            self._type_widget.setEnabled(False)
        else:
            # Change to an image type if flow is currently selected
            if self._type_widget.get_input()[0] == inspector.DataType.FLOW:
                self._type_widget.set_value(inspector.DataType.COLOR)
            self._type_widget.setEnabled(True)
        self._btn_confirm.setEnabled(self._filename is not None)
        if self._filename is None:
            self.__onCancel()

    @pyqtSlot()
    def __onCancel(self):
        self.reject()

    @pyqtSlot()
    def __onConfirm(self):
        type_tuple = self._type_widget.get_input()
        if type_tuple is None:
            self._data_type = None
        else:
            self._data_type = type_tuple[0]
        self._confirmed = True
        self.accept()

    def getSelection(self):
        if self._confirmed:
            return (self._filename, self._data_type)
        return None


class SaveInspectionFileDialog(QDialog):
    SAVE_VISUALIZATION = 0
    SAVE_RAW = 1

    def __init__(self, data_type, thumbnails=None, parent=None):
        super(SaveInspectionFileDialog, self).__init__(parent)
        """
        Dialog to save raw data or current visualization to disk.

        data_type:  None or inspector.DataType, is used to select the initial
                    file filter.
        thumbnail:  None or dictionary of {key: QPixmap}, providing one thumbnail
                    image for each of the available save types, i.e. SAVE_RAW and
                    SAVE_VISUALIZATION. The thumbnail corresponding to the user's
                    selection Will be shown on the dialog so s/he knows, what will
                    be saved.
        """
        self._filename = None
        self._save_as = None
        self._confirmed = False
        self._thumbnails = thumbnails
        self._thumbnail_viewer = None
        self.__prepareLayout(data_type)

    def __prepareLayout(self, data_type):
        self.setWindowTitle('Save File')
        layout = QVBoxLayout()
        file_filters = 'Images (*.bmp *.jpg *.jpeg *.png *.ppm);;Optical Flow (*.flo);;NumPy Arrays (*.npy);;All Files (*.*)'
        if data_type == inspector.DataType.FLOW:
            initial_filter = 'Optical Flow (*.flo)'
        elif data_type == inspector.DataType.MULTICHANNEL:
            initial_filter = 'NumPy Arrays (*.npy)'
        else:
            initial_filter = 'Images (*.bmp *.jpg *.jpeg *.png *.ppm)'
        self._file_widget = inputs.SelectDirEntryWidget('File:',
            inputs.SelectDirEntryType.FILENAME_SAVE, parent=self,
            filters=file_filters,
            initial_filter=initial_filter,
            min_label_width=None, relative_base_path=None)
        self._file_widget.value_changed.connect(self.__fileSelected)
        layout.addWidget(self._file_widget)

        self._save_as_widget = inputs.DropDownSelectionWidget('What to save:',
            [(SaveInspectionFileDialog.SAVE_VISUALIZATION, 'Current visualization'),
            (SaveInspectionFileDialog.SAVE_RAW, 'Input data')])
        self._save_as_widget.value_changed.connect(self.__updateThumbnail)
        layout.addWidget(self._save_as_widget)

        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton('Cancel')
        btn_cancel.clicked.connect(self.__onCancel)
        btn_layout.addWidget(btn_cancel)

        self._btn_confirm = QPushButton('Save')
        self._btn_confirm.clicked.connect(self.__onConfirm)
        self._btn_confirm.setEnabled(False)
        btn_layout.addWidget(self._btn_confirm)

        layout.addLayout(btn_layout)
        if self._thumbnails is None:
            self.setLayout(layout)
        else:
            # Show thumbnail left of input widgets, so the user knows what
            # he is going to save.
            thumb_layout = QVBoxLayout()
            thumb_layout.addWidget(QLabel('To save:'))
            self._thumbnail_viewer = imgview.ImageLabel(
                self._thumbnails[SaveInspectionFileDialog.SAVE_VISUALIZATION])
            thumb_layout.addWidget(self._thumbnail_viewer)
            hlayout = QHBoxLayout()
            hlayout.addLayout(thumb_layout)
            hlayout.addWidget(inputs.VLine())
            hlayout.addLayout(layout)
            self.setLayout(hlayout)

    def open(self):
        super(SaveInspectionFileDialog, self).open()
        self._file_widget.open_dialog()

    @pyqtSlot(object)
    def __updateThumbnail(self, selection):
        if selection is None or self._thumbnails is None:
            return
        self._thumbnail_viewer.setPixmap(self._thumbnails[selection[0]])

    @pyqtSlot(object)
    def __fileSelected(self, filename):
        self._filename = filename
        self._btn_confirm.setEnabled(self._filename is not None)
        if self._filename is None:
            self.__onCancel()

    @pyqtSlot()
    def __onCancel(self):
        self.reject()

    @pyqtSlot()
    def __onConfirm(self):
        tpl = self._save_as_widget.get_input()
        if tpl is None:
            self._save_as = None
        else:
            self._save_as = tpl[0]
        self._confirmed = True
        self.accept()

    def getSelection(self):
        if self._confirmed:
            return (self._filename, self._save_as)
        return None


class ToolbarFileIOWidget(QWidget):
    """
    Provides buttons to issue open/save file requests.
    """
    fileOpenRequest = pyqtSignal()
    fileSaveRequest = pyqtSignal()

    def __init__(self, vertical=False, icon_size=QSize(20, 20), parent=None):
        """
        Shows two clickable icons to open a file and save the currently
        inspected data to disk.
        Buttons can be arranged horizontally or vertially, set the "vertical"
        flag accordingly.
        The "icon_size" parameter specifies the icon size. Suggested defaults
        are 20x20 if widget is placed inside the status bar, 24x24 otherwise.
        """
        super(ToolbarFileIOWidget, self).__init__(parent)
        if vertical:
            layout = QVBoxLayout()
        else:
            layout = QHBoxLayout()
        # Add "Open File" button
        btn = QToolButton()
        # To look up names of theme icons, see
        # https://specifications.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html
        btn.setIcon(QIcon.fromTheme('document-open'))
        btn.setIconSize(icon_size)
        btn.setToolTip('Open file (Ctrl+O)')
        btn.clicked.connect(self.fileOpenRequest)
        layout.addWidget(btn)

        # Add "Save as..." button
        btn = QToolButton()
        btn.setIcon(QIcon.fromTheme('document-save-as'))
        btn.setIconSize(icon_size)
        btn.setToolTip('Save as... (Ctrl+S)')
        btn.clicked.connect(self.fileSaveRequest)
        layout.addWidget(btn)
        if vertical:
            layout.setAlignment(Qt.AlignTop)
        else:
            layout.setAlignment(Qt.AlignRight)
        # Important to avoid unnecessary widget margins:
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)


class ToolbarZoomWidget(QWidget):
    """
    Provides two clickable icons allowing the user to request the standard
    scalings "zoom-best-fit" (fit image to the currently available canvas
    size) and "zoom-original" (show image at 100% zoom).
    """
    # Signal if zoom-best-fit is clicked
    zoomBestFitRequest = pyqtSignal()
    # Signal if zoom-original is clicked
    zoomOriginalSizeRequest = pyqtSignal()

    def __init__(self, central_widget, parent=None):
        super(ToolbarZoomWidget, self).__init__(parent)
        self._show_label = True
        layout = QHBoxLayout()
        self._scale_label = QLabel('Scale:')
        layout.addWidget(self._scale_label)
        btn_fit = QToolButton(central_widget)
        btn_fit.setIcon(QIcon.fromTheme('zoom-fit-best'))
        btn_fit.setIconSize(QSize(20, 20))
        btn_fit.setToolTip('Zoom to fit visible area (Ctrl+F)')
        btn_fit.clicked.connect(self.zoomBestFitRequest)
        layout.addWidget(btn_fit)

        btn_original = QToolButton(central_widget)
        btn_original.setIcon(QIcon.fromTheme('zoom-original'))
        btn_original.setIconSize(QSize(20, 20))
        btn_original.setToolTip('Zoom to original size (Ctrl+1)')
        btn_original.clicked.connect(self.zoomOriginalSizeRequest)
        layout.addWidget(btn_original)
        # Important: remove margins!
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    @pyqtSlot(float)
    def setScale(self, scale):
        if not self._show_label:
            return
        if scale < 0.01:
            self._scale_label.setText('Scale < 1 %')
        else:
            self._scale_label.setText('Scale {:d} %'.format(int(scale*100)))

    def showScaleLabel(self, visible):
        self._show_label = visible
        self._scale_label.setVisible(visible)
