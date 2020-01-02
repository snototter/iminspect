#!/usr/bin/env python
# coding=utf-8
"""Inspect matrix/image data"""
#TODO ctrl+s(ave) flosave, imsave...
#TODO Test saving: color, monochrome, 16bit, depth vs categoric, bool, flow
#TODO implement above, then deploy
import numpy as np
from enum import Enum
import qimage2ndarray
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, \
    QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFrame, QToolTip, \
    QShortcut, QDialog, QErrorMessage
from PyQt5.QtCore import Qt, QSize, QRect, QPoint, QPointF, pyqtSlot
from PyQt5.QtGui import QPainter, QCursor, QFont, QBrush, QColor, \
    QKeySequence, QPixmap

from vito import imutils
from vito import colormaps
from vito import imvis
from vito import flowutils

from . import imgview as imgview
from . import inputs as inputs


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
    return '{:d}'.format(int(v))


def fmtb(v):
    return 'True' if v else 'False'


def best_format_fx(limits):
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

    def setBoolean(self, b):
        # If the visualized data is boolean, set this to True!
        self._is_boolean = b

    def setCategories(self, c):
        # If the visualized data is categoric (i.e. a label image), set the unique categories!
        self._categories = c

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
        qp.setFont(QFont('sans-serif', self._font_size))

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
            # Now the label positions are computed from largest to smallest, but
            # categories are listed from smallest to largest, so:
            label_pos.reverse()
            # Draw labels (vertically centered on corresponding filled rects)
            # Check, if all labels fit (font size vs widget height).
            height_per_label = max(size.height() / num_categories, 2*self._font_size)
            num_labels = min(num_categories, int(size.height() / height_per_label))
            # If there's too little space, select a subset of labels (and their
            # corresponding text positions).
            selected_idx = np.linspace(0, num_categories-1, num_labels)
            labels = [self._categories[int(i)] for i in selected_idx]
            lpos = [label_pos[int(i)] for i in selected_idx]
            for i in range(num_labels):
                qp.drawText(lpos[i], fmti(labels[i]))
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
            qimage = qimage2ndarray.array2qimage(colorized)
            qpixmap = QPixmap.fromImage(qimage)
            qp.drawPixmap(center.x() - radius, center.y() - radius, qpixmap)
            # Label it
            txt_height = int((size.height() - 2*self._bar_padding - diameter - 5) / 2)
            if txt_height > 15:
                qp.drawText(QRect(center.x() - radius, self._bar_padding, diameter, txt_height),
                    Qt.AlignHCenter | Qt.AlignBottom, 'Flow\nColor Wheel')
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
            fmt = best_format_fx(self._limits)
            height_per_label = max(size.height() / self._num_labels, 2*self._font_size)
            num_labels = min(self._num_labels, int(size.height() / height_per_label))
            labels = np.linspace(self._limits[0], self._limits[1], num_labels)
            for i in range(num_labels):
                pos = QPoint(2*self._bar_padding + self._bar_width,
                             int(size.height() - i * (size.height()-self._font_size)/(num_labels-1)))
                qp.drawText(pos, fmt(labels[i]))
        # We're done painting
        qp.end()


class DataType(Enum):
    COLOR = 0
    MONOCHROME = 1
    BOOL = 2
    CATEGORIC = 3
    FLOW = 4
    DEPTH = 5

    @staticmethod
    def toStr(dt):
        """Human-readable string representation of DataType enum."""
        if dt == DataType.COLOR:
            return 'color'
        elif dt == DataType.MONOCHROME:
            return 'monochrome'
        elif dt == DataType.BOOL:
            return 'mask'
        elif dt == DataType.CATEGORIC:
            return 'labels'
        elif dt == DataType.FLOW:
            return 'flow'
        elif dt == DataType.DEPTH:
            return 'depth'
        else:
            raise ValueError('Invalid DataType')

    @staticmethod
    def fromData(npdata):
        """Make a best guess on the proper data type given the numpy ndarray
        input npdata. In particular, we consider npdata.ndim and dtype:
        * HxW or HxWx1
            * data.dtype is bool: DataType.BOOL
            * data.dtype in {uint8, float32, float64}: DataType.MONOCHROME
            * data.dtype in {uint16, int32}: DataType.DEPTH
            * else: DataType.CATEGORIC
        * HxWx2: DataType.FLOW
        * HxWx3: DataType.COLOR
        """
        if npdata.ndim < 3 or (npdata.ndim == 3 and npdata.shape[2] == 1):
            if npdata.dtype is np.dtype('bool'):
                return DataType.BOOL
            elif npdata.dtype in [np.dtype('uint8'), np.dtype('float32'), np.dtype('float64')]:
                return DataType.MONOCHROME
            elif npdata.dtype in [np.dtype('uint16'), np.dtype('int32')]:
                return DataType.DEPTH
            else:
                return DataType.CATEGORIC
        elif npdata.ndim == 3:
            if npdata.shape[2] == 2:
                return DataType.FLOW
            elif npdata.shape[2] == 3:
                return DataType.COLOR
            else:
                raise ValueError('Input data with %d channels is not supported' % npdata.shape[2])
        else:
            raise ValueError('Input data with ndim > 3 (i.e. %d) is not supported!' % npdata.ndim)


class OpenInspectionFileDialog(QDialog):
    def __init__(self, data_type=None, parent=None):
        super(OpenInspectionFileDialog, self).__init__(parent)
        self._filename = None
        self._data_type = None
        self._confirmed = False
        self._prepareLayout(data_type)

    def _prepareLayout(self, current_data_type):
        self.setWindowTitle('Open File')
        layout = QVBoxLayout()
        file_filters = 'Images (*.bmp *.jpg *.jpeg *.png *.ppm);;Optical Flow (*.flo);;All Files (*.*)'
        self._file_widget = inputs.SelectDirEntryWidget('File:',
            inputs.SelectDirEntryType.FILENAME_OPEN, parent=self,
            filters=file_filters,
            initial_filter='' if current_data_type is None or current_data_type != DataType.FLOW else 'Optical Flow (*.flo)',
            min_label_width=None, relative_base_path=None)
        self._file_widget.value_changed.connect(self._fileSelected)
        layout.addWidget(self._file_widget)

        self._type_widget = inputs.DropDownSelectionWidget('Type:',
            [(DataType.COLOR, 'Color'),
            (DataType.MONOCHROME, 'Monochrome'),
            (DataType.BOOL, 'Boolean Mask'),
            (DataType.CATEGORIC, 'Categories / Labels'),
            (DataType.DEPTH, 'Depth'),
            (DataType.FLOW, 'Optical Flow')])
        if current_data_type is not None:
            self._type_widget.set_value(current_data_type)
        layout.addWidget(self._type_widget)

        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton('Cancel')
        btn_cancel.clicked.connect(self._onCancel)
        btn_layout.addWidget(btn_cancel)

        self._btn_confirm = QPushButton('Open')
        self._btn_confirm.clicked.connect(self._onConfirm)
        self._btn_confirm.setEnabled(False)
        btn_layout.addWidget(self._btn_confirm)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def open(self):
        super(OpenInspectionFileDialog, self).open()
        self._file_widget.open_dialog()

    @pyqtSlot(object)
    def _fileSelected(self, filename):
        self._filename = filename
        if self._filename is not None and self._filename.endswith('.flo'):
            self._type_widget.set_value(DataType.FLOW)
            self._type_widget.setEnabled(False)
        else:
            # Change to an image type if flow was selected
            if self._type_widget.get_input()[0] == DataType.FLOW:
                self._type_widget.set_value(DataType.COLOR)
            self._type_widget.setEnabled(True)
        self._btn_confirm.setEnabled(self._filename is not None)

    @pyqtSlot()
    def _onCancel(self):
        self.reject()

    @pyqtSlot()
    def _onConfirm(self):
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


class Inspector(QMainWindow):
    """Opens GUI to inspect the given data"""

    # Identifiers for visualization drop down
    VIS_RAW = -1
    # Ensure that grayscale is the second option
    VIS_COLORMAPS = ['Grayscale'] + [cmn for cmn in colormaps.colormap_names if cmn.lower() != 'grayscale']

    @staticmethod
    def makeWindowTitle(label, data_type):
        if data_type is None:
            raise ValueError('Input data_type cannot be None!')
        if label is None:
            return 'Data Inspection [{}]'.format(DataType.toStr(data_type))
        else:
            return label

    def __init__(
            self, data, data_type, display_settings=None,
            initial_window_size=QSize(1280, 720), window_title=None):
        super(Inspector, self).__init__()
        self._initial_window_size = initial_window_size
        self._window_title = window_title
        self._shortcuts = list()
        self._open_file_dialog = None
        # All other internal fields are declared and set in inspectData:
        self.inspectData(data, data_type, display_settings)

    def inspectData(self, data, data_type, display_settings=None):
        self._data = data                    # The raw data
        self._data_type = DataType.fromData(data) if data_type is None else data_type

        self._visualized_data = None         # Currently visualized data (e.g. a single channel)
        self._visualized_pseudocolor = None  # Currently visualized pseudocolorized data
        self._reset_viewer = True            # Whether the image viewer should be reset (adjust size and translation)

        self._is_single_channel = (data.ndim < 3) or (data.shape[2] == 1)

        # Set up GUI
        self._resetLayout()
        self._prepareActions()
        # Analyze the given data (range, data type, channels, etc.)
        self._prepareDataStatistics()
        # Now we're ready to visualize the data
        self._updateDisplay()
        # Restore display settings
        self.restoreDisplaySettings(display_settings)

    def _prepareDataStatistics(self):
        """Analyzes the internal _data field (range, data type, channels,
        etc.) and sets member variables accordingly.
        Additionally, information will be printed to stdout and shown on
        the GUI.
        """
        self._data_limits = [np.min(self._data[:]), np.max(self._data[:])]

        stdout_str = list()
        stdout_str.append('##################################################\nData inspection:\n')
        stdout_str.append('Data type: {} ({})'.format(
            self._data.dtype, DataType.toStr(self._data_type)))
        stdout_str.append('Shape:     {}\n'.format(self._data.shape))

        lbl_txt = '<table cellpadding="5"><tr><th colspan="2">Information</th></tr>'
        lbl_txt += '<tr><td>Type: {} ({})</td><td>Shape: {}</td></tr>'.format(
            self._data.dtype, DataType.toStr(self._data_type), self._data.shape)

        # Select format function to display data in status bar/tooltip
        if self._data_type == DataType.BOOL:
            self._data_limits = [float(v) for v in self._data_limits]
            self.__fmt_fx = fmtb
            self._colorbar.setBoolean(True)
        elif self._data_type == DataType.CATEGORIC:
            self.__fmt_fx = fmti
            self._data_categories, ic = np.unique(self._data, return_inverse=True)
            self._data_inverse_categories = ic.reshape(self._data.shape)
            self._colorbar.setCategories(self._data_categories)
        else:
            self.__fmt_fx = best_format_fx(self._data_limits)

        # Prepare QLabel and stdout message:
        if self._data_type == DataType.BOOL:
            lbl_txt += '<tr><td colspan="2">Binary mask.</td></tr>'
        elif self._data_type == DataType.CATEGORIC:
            stdout_str.append('This is a categoric/label image with {:d} categories'.format(len(self._data_categories)))
            lbl_txt += '<tr><td colspan="2">Label image, {:d} classes.</td></tr>'.format(len(self._data_categories))
        else:
            global_mean = np.mean(self._data[:])
            global_std = np.std(self._data[:])
            #
            stdout_str.append('Minimum: {}'.format(self._data_limits[0]))
            stdout_str.append('Maximum: {}'.format(self._data_limits[1]))
            stdout_str.append('Mean:    {} +/- {}\n'.format(global_mean, global_std))
            #
            lbl_txt += '<tr><td>Range: [{}, {}]</td><td>Mean: {} &#177; {}</td></tr>'.format(
                self.__fmt_fx(self._data_limits[0]),
                self.__fmt_fx(self._data_limits[1]),
                self.__fmt_fx(global_mean),
                self.__fmt_fx(global_std))

            if not self._is_single_channel:
                for c in range(self._data.shape[2]):
                    cmin = np.min(self._data[:, :, c])
                    cmax = np.max(self._data[:, :, c])
                    cmean = np.mean(self._data[:, :, c])
                    cstd = np.std(self._data[:, :, c])
                    #
                    stdout_str.append('Minimum on channel {}: {}'.format(c, cmin))
                    stdout_str.append('Maximum on channel {}: {}'.format(c, cmax))
                    stdout_str.append('Mean on channel {}:    {} +/- {}\n'.format(c, cmean, cstd))
                    #
                    lbl_txt += '<tr><td>Channel {} range: [{}, {}]</td><td>Mean: {} &#177; {}</td></tr>'.format(
                        c, self.__fmt_fx(cmin), self.__fmt_fx(cmax), self.__fmt_fx(cmean), self.__fmt_fx(cstd))

        # Print to stdout
        for s in stdout_str:
            print(s)
        # Show on label
        lbl_txt += '</table>'
        self._data_label.setText(lbl_txt)

    def currentDisplaySettings(self):
        settings = {
            'wsize': self.size(),
            'screenpos': self.mapToGlobal(QPoint(0, 0)),
            'dd:vis': self._visualization_dropdown.get_input()[0],
            'data_type': self._data_type
        }
        if not self._is_single_channel:
            settings['dd:layer'] = self._layer_dropdown.get_input()[0]
            settings['cb:globlim'] = self._checkbox_global_limits.get_input()
        settings.update(self._img_viewer.currentDisplaySettings())
        return settings

    def restoreDisplaySettings(self, settings):
        if settings is None:
            return
        # Restore customized UI settings (only if data type didn't change)
        if self._data_type == settings['data_type']:
            self._visualization_dropdown.set_value(settings['dd:vis'])
            if not self._is_single_channel:
                self._layer_dropdown.set_value(settings['dd:layer'])
                self._checkbox_global_limits.set_value(settings['cb:globlim'])
        # Restore window position/dimension
        self.resize(settings['wsize'])
        # Note that restoring the position doesn't always work (issues with
        # windows that are placed partially outside the screen)
        self.move(settings['screenpos'])
        # Restore zoom/translation settings
        self._img_viewer.restoreDisplaySettings(settings)
        self._updateDisplay()

    def _resetLayout(self):
        self._main_widget = QWidget()
        input_layout = QVBoxLayout()

        # Let user select a single channel if multi-channel input is provided
        if not self._is_single_channel:
            if self._data_type == DataType.FLOW and self._data.shape[2] == 2:
                dd_options = [(-1, 'All'), (0, 'Horizontal'), (1, 'Vertical')]
            else:
                dd_options = [(-1, 'All')] + [(c, 'Layer {:d}'.format(c)) for c in range(self._data.shape[2])]
            self._layer_dropdown = inputs.DropDownSelectionWidget('Select layer:', dd_options)
            self._layer_dropdown.value_changed.connect(self._updateDisplay)
            input_layout.addWidget(self._layer_dropdown)

        if self._is_single_channel or self._data_type == DataType.CATEGORIC:
            self._checkbox_global_limits = None
        else:
            self._checkbox_global_limits = inputs.CheckBoxWidget(
                'Use same visualization limits for all channels:',
                checkbox_left=False, is_checked=True)
            input_layout.addWidget(self._checkbox_global_limits)
            self._checkbox_global_limits.value_changed.connect(self._updateDisplay)

        # Let user select the visualization method
        vis_options = [(Inspector.VIS_RAW, 'Raw data'), (0, 'Grayscale')] + \
            [(i, 'Pseudocolor {:s}'.format(Inspector.VIS_COLORMAPS[i]))
                for i in range(1, len(Inspector.VIS_COLORMAPS))]
        # Select viridis colormap by default (note missing "-1", because we
        # prepend the "raw" option) for single channel. Default to turbo for optical flow.
        # Otherwise, just visualize the raw data by default.
        self._visualization_dropdown = inputs.DropDownSelectionWidget('Visualization:', vis_options,
            initial_selected_index=len(Inspector.VIS_COLORMAPS) if self._is_single_channel
                else (len(Inspector.VIS_COLORMAPS)-1 if self._data_type == DataType.FLOW else 0))
        self._visualization_dropdown.value_changed.connect(self._updateDisplay)
        input_layout.addWidget(self._visualization_dropdown)

        # Layout buttons horizontally
        btn_layout = QHBoxLayout()
        # Button to allow user scaling the displayed image
        btn_scale_to_fit = QPushButton('Scale to fit window')
        btn_scale_to_fit.clicked.connect(lambda: self._img_viewer.scaleToFitWindow())
        btn_layout.addWidget(btn_scale_to_fit)

        btn_scale_original = QPushButton('Original size')
        btn_scale_original.clicked.connect(lambda: self._img_viewer.setScale(1.0))
        btn_layout.addWidget(btn_scale_original)

        input_layout.addLayout(btn_layout)

        # Label to show important image statistics/information
        self._data_label = QLabel()
        self._data_label.setFrameShape(QFrame.Panel)
        self._data_label.setFrameShadow(QFrame.Sunken)

        # Image viewer and colorbar
        img_layout = QHBoxLayout()
        self._img_viewer = imgview.ImageViewer()
        self._img_viewer.mouseMoved.connect(self._mouseMoved)
        img_layout.addWidget(self._img_viewer)

        self._colorbar = ColorBar()
        img_layout.addWidget(self._colorbar)

        # Set font of tool tips
        QToolTip.setFont(QFont('SansSerif', 10))

        # Grab a convenience handle to the status bar
        self._status_bar = self.statusBar()

        # Place the information label next to the user inputs:
        top_row_layout = QHBoxLayout()
        top_row_layout.addLayout(input_layout)
        top_row_layout.addWidget(self._data_label)
        # Set the main widget's layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_row_layout)
        main_layout.addLayout(img_layout)
        self._main_widget.setLayout(main_layout)
        self.setCentralWidget(self._main_widget)
        self.resize(self._initial_window_size)
        self.setWindowTitle(Inspector.makeWindowTitle(self._window_title, self._data_type))

    def _prepareActions(self):
        # Disable and delete previously registered shortcuts (otherwise, they
        # would be silently ignored once you replace the central widget - which
        # happens as soon as you display another image with the same Inspector
        # instance).
        for sc in self._shortcuts:
            sc.setEnabled(False)
            sc.deleteLater()
        self._shortcuts = list()
        # Open file
        self._shortcut_open = QShortcut(QKeySequence('Ctrl+O'), self)
        self._shortcut_open.activated.connect(self._onOpen)
        self._shortcuts.append(self._shortcut_open)
        # Close window
        self._shortcut_exit = QShortcut(QKeySequence('Ctrl+Q'), self)
        self._shortcut_exit.activated.connect(QApplication.instance().quit)
        self._shortcuts.append(self._shortcut_exit)
        # Zooming
        self._shortcut_zoom_in = QShortcut(QKeySequence('Ctrl++'), self)
        self._shortcut_zoom_in.activated.connect(lambda: self._img_viewer.zoom(120))
        self._shortcuts.append(self._shortcut_zoom_in)
        self._shortcut_zoom_in_fast = QShortcut(QKeySequence('Ctrl+Shift++'), self)
        self._shortcut_zoom_in_fast.activated.connect(lambda: self._img_viewer.zoom(1200))
        self._shortcuts.append(self._shortcut_zoom_in_fast)
        self._shortcut_zoom_out = QShortcut(QKeySequence('Ctrl+-'), self)
        self._shortcut_zoom_out.activated.connect(lambda: self._img_viewer.zoom(-120))
        self._shortcuts.append(self._shortcut_zoom_out)
        self._shortcut_zoom_out_fast = QShortcut(QKeySequence('Ctrl+Shift+-'), self)
        self._shortcut_zoom_out_fast.activated.connect(lambda: self._img_viewer.zoom(-1200))
        self._shortcuts.append(self._shortcut_zoom_out_fast)
        # Scrolling
        self._shortcut_scroll_up = QShortcut(QKeySequence('Ctrl+Up'), self)
        self._shortcut_scroll_up.activated.connect(lambda: self._img_viewer.scroll(120, Qt.Vertical))
        self._shortcuts.append(self._shortcut_scroll_up)
        self._shortcut_scroll_up_fast = QShortcut(QKeySequence('Ctrl+Shift+Up'), self)
        self._shortcut_scroll_up_fast.activated.connect(lambda: self._img_viewer.scroll(1200, Qt.Vertical))
        self._shortcuts.append(self._shortcut_scroll_up_fast)
        self._shortcut_scroll_down = QShortcut(QKeySequence('Ctrl+Down'), self)
        self._shortcut_scroll_down.activated.connect(lambda: self._img_viewer.scroll(-120, Qt.Vertical))
        self._shortcuts.append(self._shortcut_scroll_down)
        self._shortcut_scroll_down_fast = QShortcut(QKeySequence('Ctrl+Shift+Down'), self)
        self._shortcut_scroll_down_fast.activated.connect(lambda: self._img_viewer.scroll(-1200, Qt.Vertical))
        self._shortcuts.append(self._shortcut_scroll_down_fast)
        self._shortcut_scroll_left = QShortcut(QKeySequence('Ctrl+Left'), self)
        self._shortcut_scroll_left.activated.connect(lambda: self._img_viewer.scroll(120, Qt.Horizontal))
        self._shortcuts.append(self._shortcut_scroll_left)
        self._shortcut_scroll_left_fast = QShortcut(QKeySequence('Ctrl+Shift+Left'), self)
        self._shortcut_scroll_left_fast.activated.connect(lambda: self._img_viewer.scroll(1200, Qt.Horizontal))
        self._shortcuts.append(self._shortcut_scroll_left_fast)
        self._shortcut_scroll_right = QShortcut(QKeySequence('Ctrl+Right'), self)
        self._shortcut_scroll_right.activated.connect(lambda: self._img_viewer.scroll(-120, Qt.Horizontal))
        self._shortcuts.append(self._shortcut_scroll_right)
        self._shortcut_scroll_right_fast = QShortcut(QKeySequence('Ctrl+Shift+Right'), self)
        self._shortcut_scroll_right_fast.activated.connect(lambda: self._img_viewer.scroll(-1200, Qt.Horizontal))
        self._shortcuts.append(self._shortcut_scroll_right_fast)
        # Scale to fit window
        self._shortcut_scale_fit = QShortcut(QKeySequence('Ctrl+F'), self)
        self._shortcut_scale_fit.activated.connect(self._img_viewer.scaleToFitWindow)
        self._shortcuts.append(self._shortcut_scale_fit)
        self._shortcut_scale_original = QShortcut(QKeySequence('Ctrl+1'), self)
        self._shortcut_scale_original.activated.connect(lambda: self._img_viewer.setScale(1.0))
        self._shortcuts.append(self._shortcut_scale_original)

    @pyqtSlot()
    def _updateDisplay(self):
        # Select which layer to show:
        if self._is_single_channel:
            self._visualized_data = self._data
            is_single_channel = True
        else:
            layer_selection = self._layer_dropdown.get_input()[0]
            if layer_selection < 0:
                self._visualized_data = self._data
                is_single_channel = False
            else:
                self._visualized_data = self._data[:, :, layer_selection]
                is_single_channel = True

        # Reset pseudocolor if visualization input is multi-channel
        if is_single_channel:
            self._visualization_dropdown.setEnabled(True)
        else:
            self._visualization_dropdown.setEnabled(False)

        # Select visualization mode
        vis_selection = self._visualization_dropdown.get_input()[0]
        if vis_selection == Inspector.VIS_RAW or not is_single_channel:
            if not is_single_channel and self._data_type == DataType.FLOW:
                self._visualized_pseudocolor = flowutils.colorize_flow(self._visualized_data)
                self._img_viewer.showImage(self._visualized_pseudocolor)
                self._colorbar.setFlowWheel(True)
                self._colorbar.setVisible(True)
                self._colorbar.update()
            else:
                self._img_viewer.showImage(self._visualized_data, adjust_size=self._reset_viewer)
                self._colorbar.setVisible(False)
                self._visualized_pseudocolor = None
        else:
            cm = colormaps.by_name(Inspector.VIS_COLORMAPS[vis_selection])

            if self._data_type == DataType.CATEGORIC:
                pc = imvis.pseudocolor(self._data_inverse_categories,
                    color_map=cm, limits=[0, len(self._data_categories)-1])
            else:
                if self._checkbox_global_limits is not None \
                        and self._checkbox_global_limits.get_input():
                    limits = self._data_limits
                else:
                    limits = [np.min(self._visualized_data[:]), np.max(self._visualized_data[:])]
                    if self._data.dtype is np.dtype('bool'):
                        limits = [float(v) for v in limits]
                self._colorbar.setLimits(limits)
                pc = imvis.pseudocolor(self._visualized_data, color_map=cm, limits=limits)
            self._visualized_pseudocolor = pc
            self._img_viewer.showImage(pc, adjust_size=self._reset_viewer)
            self._colorbar.setColormap(cm)
            self._colorbar.setFlowWheel(False)
            self._colorbar.setVisible(True)
            self._colorbar.update()
        self._reset_viewer = False

    def _queryDataLocation(self, px_x, px_y):
        """Retrieves the image data at location (px_x, px_y)."""
        x = int(px_x)
        y = int(px_y)
        if x < 0 or x >= self._data.shape[1] or y < 0 or y >= self._data.shape[0]:
            return None
        query = dict()
        query['pos'] = '({:d}, {:d})'.format(x, y)

        # Representation of raw data
        query['currlayer'] = None
        if self._is_single_channel:
            query['rawstr'] = self.__fmt_fx(self._data[y, x])
        else:
            query['rawstr'] = '[' + ', '.join([self.__fmt_fx(
                self._data[y, x, c])
                for c in range(self._data.shape[2])]) + ']'
            # Representation of currently visualized data (if different from raw)
            if self._layer_dropdown.get_input()[0] >= 0:
                if len(self._visualized_data.shape) == 2:
                    query['currlayer'] = self.__fmt_fx(self._visualized_data[y, x])
                else:
                    if self._visualized_data.shape[2] != 1:
                        raise RuntimeError('Invalid number of channels')
                    query['currlayer'] = self.__fmt_fx(self._visualized_data[y, x, 0])

        if self._visualized_pseudocolor is None:
            query['pseudocol'] = None
        else:
            query['pseudocol'] = '[' + ', '.join(
                ['{:d}'.format(self._visualized_pseudocolor[y, x, c])
                    for c in range(self._visualized_pseudocolor.shape[2])]) \
                    + ']'
        return query

    def _statusBarMessage(self, query):
        """Returns a message to be displayed upon the status bar showing
        the data point at the cursor position. Requires result of _queryDataLocation
        as input.
        """
        s = query['pos'] + ', ' + ('Category' if self._data_type == DataType.CATEGORIC
            else ('Flow' if self._data_type == DataType.FLOW else 'Raw data'))\
            + ': ' + query['rawstr']
        if query['currlayer'] is not None:
            s += ', Current layer: ' + query['currlayer']
        if query['pseudocol'] is not None:
            s += ', Pseudocolor: ' + query['pseudocol']
        return s

    def _tooltipMessage(self, query):
        """Returns a HTML formatted tooltip message showing the
        data point at the cursor position. Requires result of _queryDataLocation
        as input.
        """
        s = '<table><tr><td>Position:</td><td>' + query['pos'] + '</td></tr>'
        s += '<tr><td>' + ('Category' if self._data_type == DataType.CATEGORIC
            else ('Flow' if self._data_type == DataType.FLOW else 'Raw data')) \
            + ':</td><td>' + query['rawstr'] + '</td></tr>'
        if query['currlayer'] is not None:
            s += '<tr><td>Layer:</td><td>' + query['currlayer'] + '</td></tr>'
        if query['pseudocol'] is not None:
            s += '<tr><td>Colormap:</td><td> ' + query['pseudocol'] + '</td></tr>'
        scale = self._img_viewer.currentImageScale()
        if scale != 1.0:
            s += '<tr><td>Scale:</td><td>' + ('&lt; 1' if scale < 0.01 else '{:d}'.format(int(scale*100))) + ' %</td></tr>'
        s += '</table>'
        return s

    @pyqtSlot(QPointF)
    def _mouseMoved(self, image_pos):
        """Invoked whenever the mouse position changed."""
        q = self._queryDataLocation(image_pos.x(), image_pos.y())
        if q is None:
            return
        self._status_bar.showMessage(self._statusBarMessage(q))
        QToolTip.showText(QCursor().pos(), self._tooltipMessage(q))

    @pyqtSlot()
    def _onOpen(self):
        self._open_file_dialog = OpenInspectionFileDialog(
            data_type=self._data_type, parent=self)
        self._open_file_dialog.finished.connect(self._onOpenFinished)
        self._open_file_dialog.open()

    @pyqtSlot()
    def _onOpenFinished(self):
        res = self._open_file_dialog.getSelection()
        if res is None:
            return
        try:
            filename, data_type = res
            if data_type == DataType.FLOW:
                data = flowutils.floread(filename)
            else:
                im_mode = {
                    DataType.COLOR: 'RGB',
                    DataType.MONOCHROME: 'L',
                    DataType.CATEGORIC: 'I',
                    DataType.BOOL: 'L',
                    DataType.DEPTH: 'I'
                }
                data = imutils.imread(filename, mode=im_mode[data_type])
                if data_type == DataType.BOOL:
                    data = data.astype(np.bool)
            self.setWindowTitle(Inspector.makeWindowTitle(self._window_title, data_type))
            current_display = self.currentDisplaySettings()
            self.inspectData(data, data_type, display_settings=current_display)
        except Exception as e:
            error_dialog = QErrorMessage()
            error_dialog.setWindowTitle('Error loading "{:s}"'.format(DataType.toStr(data_type)))
            error_dialog.showMessage('Cannot load "{:s}" as "{:s}":\n{:s}'.format(
                filename,
                DataType.toStr(data_type),
                str(e)
            ))
            error_dialog.exec_()


def inspect(
        data,
        data_type=None,
        flip_channels=False,
        label=None,
        display_settings=None,
        initial_window_size=QSize(1280, 720)):
    """Opens a GUI to visualize the given image data.

    data:          numpy ndarray to be visualized.
    data_type:     One of the DataType enumeration or None.
                   Useful if you want to show a label image - there's no (easy)
                   way of automatically distinguish a monochrome image from
                   a label image if you provide a uint8 input...
                   If None, the "Inspector" will try to guess the data type from
                   the input data.shape and data.dtype:
                   * HxW or HxWx1
                     * data.dtype is bool: DataType.BOOL
                     * data.dtype in {uint8, float32, float64}: DataType.MONOCHROME
                     * data.dtype in {uint16, int32}: DataType.DEPTH
                     * else: DataType.CATEGORIC
                   * HxWx2: DataType.FLOW
                   * HxWx3: DataType.COLOR

                   For example, if you have an int32 image you want to visualize
                   as class labels, specify data_type=DataType.CATEGORIC. The
                   inspector's guess would be depth data.
    flip_channels: this qt window works with RGB images, so flip_channels must
                   be set True if your data is BGR.
    label:         optional window title.
    display_settings: a dictionary of display settings in case you want to
                   restore the previous settings. The current settings are
                   returned by this function.
    initial_window_size: Resize the window.

    returns: the window's exit code and a dictionary of currently used display
             settings.
    """
    if flip_channels:
        data = imutils.flip_layers(data)
    # If window title is not provided, make one (indicating the data type).
    if data_type is None:
        app_label = Inspector.makeWindowTitle(label, DataType.fromData(data))
    else:
        app_label = Inspector.makeWindowTitle(label, data_type)

    app = QApplication([app_label])
    main_widget = Inspector(data, data_type=data_type,
        display_settings=display_settings,
        initial_window_size=initial_window_size,
        window_title=label)
    main_widget.show()
    rc = app.exec_()
    # Query the viewer settings (in case the user wants to restore them for the
    # next image)
    display_settings = main_widget.currentDisplaySettings()
    return rc, display_settings


if __name__ == '__main__':
    print('Please refer to the example application at ../examples/demo.py!')
    print('If not included in your package, see https://github.com/snototter/iminspect')
