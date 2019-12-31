#!/usr/bin/env python
# coding=utf-8
"""Inspect matrix/image data"""

import numpy as np
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, \
    QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFrame, QToolTip, \
    QShortcut
from PyQt5.QtCore import Qt, QSize, QPoint, pyqtSlot
from PyQt5.QtGui import QPainter, QCursor, QFont, QBrush, QColor, \
    QKeySequence

from vito import imutils
from vito import colormaps
from vito import imvis

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
        self.setMinimumWidth(90)
        self._colormap = None
        self._limits = None
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

    def paintEvent(self, event):
        if self._colormap is None or \
               (not self._is_boolean and self._categories is None and self._limits is None):
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


class Inspector(QMainWindow):
    """Opens GUI to inspect the given data"""

    # Identifiers for visualization drop down
    VIS_RAW = -1
    VIS_GRAY = -2
    VIS_COLORMAPS = ['autumn', 'bone', 'cold', 'disparity',
        'earth', 'hot', 'hsv', 'inferno', 'jet', 'magma', 'parula',
        'pastel', 'plasma', 'sepia', 'temperature', 'thermal', 'viridis']

    def __init__(self, data, is_categoric, display_settings=None):
        super(Inspector, self).__init__()
        self._data = data                    # The raw data
        self._is_categoric = is_categoric    # Whether the data is categoric (a label image) or not
        self._visualized_data = None         # Currently visualized data (e.g. a single channel)
        self._visualized_pseudocolor = None  # Currently visualized pseudocolorized data
        self._reset_viewer = True            # Flag to reset (adjust size and translation) the image viewer

        # Set up GUI
        self._prepareLayout()
        self._prepareActions()
        # Analyze the given data (range, data type, channels, etc.)
        self._queryStatistics()
        # Now we're ready to visualize the data
        self._updateDisplay()
        # Restore display settings
        self.restoreDisplaySettings(display_settings)

    def _queryStatistics(self):
        """Analyzes the internal _data field (range, data type, channels,
        etc.) and sets member variables accordingly.
        Additionally, information will be printed to stdout and shown on
        the GUI.
        """
        self._data_limits = [np.min(self._data[:]), np.max(self._data[:])]

        stdout_str = list()
        stdout_str.append('##################################################\nData inspection:\n')
        stdout_str.append('Data type: {}'.format(self._data.dtype))
        stdout_str.append('Shape:     {}\n'.format(self._data.shape))
        #
        lbl_txt = '<table cellpadding="5"><tr><th colspan="2">Information</th></tr>'
        lbl_txt += '<tr><td>Type: {}</td><td>Shape: {}</td></tr>'.format(self._data.dtype, self._data.shape)

        # Select format function to display data in status bar/tooltip
        if self._data.dtype == np.bool:
            self._data_limits = [float(v) for v in self._data_limits]
            self.__fmt_fx = fmtb
            self._colorbar.setBoolean(True)
        elif self._is_categoric:
            self.__fmt_fx = fmti
            self._data_categories, ic = np.unique(self._data, return_inverse=True)
            self._data_inverse_categories = ic.reshape(self._data.shape)
            self._colorbar.setCategories(self._data_categories)
        else:
            self.__fmt_fx = best_format_fx(self._data_limits)

        if self._is_categoric:
            stdout_str.append('This is a categoric/label image with {:d} categories'.format(len(self._data_categories)))
            lbl_txt += '<tr><td colspan="2">Label image, {:d} classes.</td></tr>'.format(len(self._data_categories))
        elif self._data.dtype == np.bool:
            lbl_txt += '<tr><td colspan="2">Binary mask.</td></tr>'
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
            'dd:vis': self._visualization_dropdown.get_input()[0]
        }
        if not self._is_single_channel:
            settings['dd:layer'] = self._layer_dropdown.get_input()[0]
            settings['cb:globlim'] = self._checkbox_global_limits.get_input()
        settings.update(self._img_viewer.currentDisplaySettings())
        return settings

    def restoreDisplaySettings(self, settings):
        if settings is None:
            return
        # Restore customized UI settings
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

    def _prepareLayout(self):
        self._main_widget = QWidget()
        input_layout = QVBoxLayout()

        # Let user select a single channel if multi-channel input is provided
        self._is_single_channel = (len(self._data.shape) == 2) or (self._data.shape[2] == 1)
        if not self._is_single_channel:
            dd_options = [(-1, 'All')] + [(c, 'Layer {:d}'.format(c)) for c in range(self._data.shape[2])]
            self._layer_dropdown = inputs.DropDownSelectionWidget('Select layer:', dd_options)
            self._layer_dropdown.value_changed.connect(self._updateDisplay)
            input_layout.addWidget(self._layer_dropdown)

        if not self._is_single_channel and not self._is_categoric:
            self._checkbox_global_limits = inputs.CheckBoxWidget(
                'Use same visualization limits for all channels:',
                checkbox_left=False, is_checked=True)
            input_layout.addWidget(self._checkbox_global_limits)
            self._checkbox_global_limits.value_changed.connect(self._updateDisplay)
        else:
            self._checkbox_global_limits = None

        # Let user select the visualization method
        vis_options = [(type(self).VIS_RAW, 'Raw data'), (type(self).VIS_GRAY, 'Grayscale')] + \
            [(i, 'Pseudocolor {:s}'.format(
                'HSV' if type(self).VIS_COLORMAPS[i] == 'hsv'
                else type(self).VIS_COLORMAPS[i].capitalize()))
                for i in range(len(type(self).VIS_COLORMAPS))]
        self._visualization_dropdown = inputs.DropDownSelectionWidget('Visualization:', vis_options,
            initial_selected_index=0 if not self._is_single_channel else len(type(self).VIS_COLORMAPS) - 1 + 2)
        self._visualization_dropdown.value_changed.connect(self._updateDisplay)
        input_layout.addWidget(self._visualization_dropdown)

        # Button to allow user scaling the displayed image
        btn_scale_to_fit = QPushButton('Scale image to fit')
        btn_scale_to_fit.clicked.connect(lambda: self._img_viewer.scaleToFitWindow())
        input_layout.addWidget(btn_scale_to_fit)

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
        self.resize(QSize(1280, 720))

    def _prepareActions(self):
        # TODO WIP: Open image from disk
        self._shortcut_open = QShortcut(QKeySequence('Ctrl+O'), self)
        self._shortcut_open.activated.connect(self._onOpen)
        # Close window
        self._shortcut_exit = QShortcut(QKeySequence('Ctrl+Q'), self)
        self._shortcut_exit.activated.connect(QApplication.instance().quit)
        # Zooming
        self._shortcut_zoom_in = QShortcut(QKeySequence('Ctrl++'), self)
        self._shortcut_zoom_in.activated.connect(lambda: self._img_viewer.zoom(120))
        self._shortcut_zoom_in_fast = QShortcut(QKeySequence('Ctrl+Shift++'), self)
        self._shortcut_zoom_in_fast.activated.connect(lambda: self._img_viewer.zoom(1200))
        self._shortcut_zoom_out = QShortcut(QKeySequence('Ctrl+-'), self)
        self._shortcut_zoom_out.activated.connect(lambda: self._img_viewer.zoom(-120))
        self._shortcut_zoom_out_fast = QShortcut(QKeySequence('Ctrl+Shift+-'), self)
        self._shortcut_zoom_out_fast.activated.connect(lambda: self._img_viewer.zoom(-1200))
        # Scrolling
        self._shortcut_scroll_up = QShortcut(QKeySequence('Ctrl+Up'), self)
        self._shortcut_scroll_up.activated.connect(lambda: self._img_viewer.scroll(120, Qt.Vertical))
        self._shortcut_scroll_up_fast = QShortcut(QKeySequence('Ctrl+Shift+Up'), self)
        self._shortcut_scroll_up_fast.activated.connect(lambda: self._img_viewer.scroll(1200, Qt.Vertical))
        self._shortcut_scroll_down = QShortcut(QKeySequence('Ctrl+Down'), self)
        self._shortcut_scroll_down.activated.connect(lambda: self._img_viewer.scroll(-120, Qt.Vertical))
        self._shortcut_scroll_down_fast = QShortcut(QKeySequence('Ctrl+Shift+Down'), self)
        self._shortcut_scroll_down_fast.activated.connect(lambda: self._img_viewer.scroll(-1200, Qt.Vertical))
        self._shortcut_scroll_left = QShortcut(QKeySequence('Ctrl+Left'), self)
        self._shortcut_scroll_left.activated.connect(lambda: self._img_viewer.scroll(120, Qt.Horizontal))
        self._shortcut_scroll_left_fast = QShortcut(QKeySequence('Ctrl+Shift+Left'), self)
        self._shortcut_scroll_left_fast.activated.connect(lambda: self._img_viewer.scroll(1200, Qt.Horizontal))
        self._shortcut_scroll_right = QShortcut(QKeySequence('Ctrl+Right'), self)
        self._shortcut_scroll_right.activated.connect(lambda: self._img_viewer.scroll(-120, Qt.Horizontal))
        self._shortcut_scroll_right_fast = QShortcut(QKeySequence('Ctrl+Shift+Right'), self)
        self._shortcut_scroll_right_fast.activated.connect(lambda: self._img_viewer.scroll(-1200, Qt.Horizontal))
        # Scale to fit window
        self._shortcut_scale_fit = QShortcut(QKeySequence('Ctrl+F'), self)
        self._shortcut_scale_fit.activated.connect(self._img_viewer.scaleToFitWindow)

    def _updateDisplay(self, *args):
        # TODO if raw ensure that num channels == 1 or 3, otherwise show dummy image/error message
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
            self._visualization_dropdown.select_index(0)
            self._visualization_dropdown.setEnabled(False)

        # Select visualization mode
        vis_selection = self._visualization_dropdown.get_input()[0]
        if vis_selection == type(self).VIS_RAW or not is_single_channel:
            self._img_viewer.showImage(self._visualized_data, adjust_size=self._reset_viewer)
            self._colorbar.setVisible(False)
            self._visualized_pseudocolor = None
        else:
            if vis_selection == type(self).VIS_GRAY:
                cm = colormaps.colormap_gray
            else:
                cm = getattr(colormaps, 'colormap_{:s}_rgb'.format(
                    type(self).VIS_COLORMAPS[vis_selection]))

            if self._is_categoric:
                pc = imvis.pseudocolor(self._data_inverse_categories,
                    color_map=cm, limits=[0, len(self._data_categories)-1])
            else:
                if self._checkbox_global_limits is not None \
                        and self._checkbox_global_limits.get_input():
                    limits = self._data_limits
                else:
                    limits = [np.min(self._visualized_data[:]), np.max(self._visualized_data[:])]
                    if self._data.dtype == np.bool:
                        limits = [float(v) for v in limits]
                self._colorbar.setLimits(limits)
                pc = imvis.pseudocolor(self._visualized_data, color_map=cm, limits=limits)
            self._visualized_pseudocolor = pc
            self._img_viewer.showImage(pc, adjust_size=self._reset_viewer)
            self._colorbar.setColormap(cm)
            self._colorbar.setVisible(True)
            self._colorbar.update()
        self._reset_viewer = False

    def _queryData(self, px_x, px_y):
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
        the data point at the cursor position. Requires result of _queryData as
        input.
        """
        s = query['pos'] + ', ' + ('Category' if self._is_categoric else 'Raw data')\
            + ': ' + query['rawstr']
        if query['currlayer'] is not None:
            s += ', Current layer: ' + query['currlayer']
        if query['pseudocol'] is not None:
            s += ', Pseudocolor: ' + query['pseudocol']
        return s

    def _tooltipMessage(self, query):
        """Returns a HTML formatted tooltip message showing the
        data point at the cursor position. Requires result of _queryData as
        input.
        """
        s = '<table><tr><td>Position:</td><td>' + query['pos'] + '</td></tr>'
        s += '<tr><td>' + ('Category' if self._is_categoric else 'Raw') + ':</td><td>'\
            + query['rawstr'] + '</td></tr>'
        if query['currlayer'] is not None:
            s += '<tr><td>Layer:</td><td>' + query['currlayer'] + '</td></tr>'
        if query['pseudocol'] is not None:
            s += '<tr><td>Colormap:</td><td> ' + query['pseudocol'] + '</td></tr>'
        scale = self._img_viewer.currentImageScale()
        if scale != 1.0:
            s += '<tr><td>Scale:</td><td>{:.2f} %</td></tr>'.format(scale*100)
        s += '</table>'
        return s

    def _mouseMoved(self, image_pos):
        """Invoked whenever the mouse position changed."""
        q = self._queryData(image_pos.x(), image_pos.y())
        if q is None:
            return
        self._status_bar.showMessage(self._statusBarMessage(q))
        QToolTip.showText(QCursor().pos(), self._tooltipMessage(q))

    @pyqtSlot()
    def _onOpen(self):
        print('Open image!!')


def inspect(
        data, label='Data Inspection', flip_channels=False,
        is_categoric=False, display_settings=None):
    """Opens a GUI to visualize the given image data.

    data:          numpy ndarray to be visualized.
    label:         window title.
    flip_channels: this qt window works with RGB images, so flip_channels must
                   be set True if your data is BGR.
    is_categoric:  I don't know a generic and elegant way of determining
                   whether the input is categoric (i.e. a label image) or if
                   you really wanted to display some integer data (e.g.
                   disparities). Thus, set this flag if you want to display a
                   label image.
    display_settings: a dictionary of display settings in case you want to
                   restore the previous settings. The current settings are
                   returned by this function.

    returns: the window's exit code and a dictionary of currently used display
             settings.
    """
    if flip_channels:
        data = imutils.flip_layers(data)
    app = QApplication([label])
    main_widget = Inspector(data, is_categoric, display_settings)
    main_widget.show()
    rc = app.exec_()
    # Query the viewer settings (in case the user wants to restore them for the
    # next image)
    display_settings = main_widget.currentDisplaySettings()
    return rc, display_settings


if __name__ == '__main__':
    print('Please refer to the example application at ../examples/inspect_demo.py!')
    print('If not included in your package, see https://github.com/snototter/iminspect')
