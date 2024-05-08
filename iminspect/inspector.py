#!/usr/bin/env python
# coding=utf-8
"""Inspect matrix/image data"""
from typing import Tuple, Union

# TODO Ideas and potential usability improvements:
# * Load multiple files via drag & drop from file browser/external image viewer
#   => requires layout reset; potential issue: variable number of inspection
#      widgets (what's the expected behavior if there are already multple widgets
#      open for inspection?)
#
# * Add input boxes to range slider for manually typing the upper/lower limits.
#   This would require forwarding the editFinished signal to the inspector - because
#   we convert the RangeSlider steps (e.g. 0..100) to the data range (e.g. -0.5..+0.5).
#
# * Usability Improvement:
#   Thumbnail in "Open File"/"Reload Visualization" dialogs could be larger.
#
# * GUI issue:
#   Initial window resize won't scale to the exact specified size.
#   QApplication().instance().processEvents() doesn't help either. The widgets
#   (e.g. image canvas) will be resized "shortly" after initializing the QMainWindow
#   for a second time. Needs thorough investigation.
#
# * Usability improvement:
#   Incrementally in-/decreasing the zoom factor worked "good enough" so far
#   however, "fast zooming" seems a bit "too fast" sometimes. Especially "fast
#   zooming" out is really fast (decreases by 50% with each wheel tick).
#
# * Usability improvement:
#   Status bar for each InspectionWidget where the pixel value is shown (i.e.
#   you can inspect a pixel value for multiple images at once).
#   However, this is only useful if the displayed images have the same size and
#   are "linked".
#
# * Usability improvement:
#   Let the user explicitly enable/disable linking of the viewers. Currently,
#   viewers will always be "linked" if all images have the same width/height.
#
# * Usability improvement:
#   Implement a range slider widget which allows the user to adjust the
#   pseudocolor value limits on-the-fly.
#
# * Usability improvement:
#   When showing multiple images, add an option to use the same visualization
#   data range across all images.
#
# * Potential (usability) issue:
#   Consider this scenario: Initially, the user may have shown two same-sized
#   images (viewer axes have been linked). Now, a differently sized image has
#   been opened. Thus, the viewers will still/again be linked which may lead
#   to minor zooming/scrolling issues.
#   Currently, I prefer not to deal with such unexpected user behavior, as
#   this increases the code complexity unnecessarily.

import numpy as np
import os
from enum import Enum
from qtpy.QtWidgets import QMainWindow, QApplication, QWidget, \
    QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QFrame, QToolTip, \
    QShortcut, QMessageBox, QScrollArea, QSizePolicy
from qtpy.QtCore import Qt, QSize, QPoint, Signal, Slot
from qtpy.QtGui import QCursor, QFont, QKeySequence, QResizeEvent, QIcon
from PIL import UnidentifiedImageError

from vito import imutils, colormaps, imvis, flowutils

from . import imgview, inputs, inspection_widgets, inspection_utils


class DataType(Enum):
    # Standard 3- or 4-channel input
    COLOR = 0
    # Single-channel data, arbitrary type
    MONOCHROME = 1
    # Single-channel data, either bool or should be considered as/cast to bool
    BOOL = 2
    # To interpret data as having a finite number of labels/categories
    CATEGORICAL = 3
    # Two-channel optical flow data
    FLOW = 4
    # Interpret data as depth, usually uint16 or int32 (since depth cameras
    # return measurements in millimeters).
    DEPTH = 5
    # To support analysing data with more than 4 (RGBA) channels:
    MULTICHANNEL = 6

    @staticmethod
    def toStr(dt):
        """Human-readable string representation of DataType enum."""
        if dt == DataType.COLOR:
            return 'color'
        elif dt == DataType.MONOCHROME:
            return 'monochrome'
        elif dt == DataType.BOOL:
            return 'mask'
        elif dt == DataType.CATEGORICAL:
            return 'labels'
        elif dt == DataType.FLOW:
            return 'flow'
        elif dt == DataType.DEPTH:
            return 'depth'
        elif dt == DataType.MULTICHANNEL:
            return 'multi-channel'
        else:
            raise NotImplementedError('DataType "%d" is not yet supported!' % dt)

    @staticmethod
    def fromData(npdata):
        """
        Make a best guess on the proper data type given the numpy ndarray
        input npdata. In particular, we consider npdata.ndim and dtype:
        * None inputs will be mapped to DataType.COLOR by default.
        * HxW or HxWx1
            * data.dtype is bool: DataType.BOOL
            * data.dtype in {uint8, float32, float64}: DataType.MONOCHROME
            * data.dtype in {uint16, int32}: DataType.DEPTH
            * else: DataType.CATEGORICAL
        * HxWx2: DataType.FLOW
        * HxWx3 or HxWx4: DataType.COLOR
        * HxWxC, C>4: DataType.MULTICHANNEL
        """
        if npdata is None:
            return DataType.COLOR
        if npdata.ndim < 3 or (npdata.ndim == 3 and npdata.shape[2] == 1):
            if npdata.dtype is np.dtype('bool'):
                return DataType.BOOL
            elif npdata.dtype in [np.dtype('uint8'), np.dtype('float32'), np.dtype('float64')]:
                return DataType.MONOCHROME
            elif npdata.dtype in [np.dtype('uint16'), np.dtype('int32')]:
                return DataType.DEPTH
            else:
                return DataType.CATEGORICAL
        elif npdata.ndim == 3:
            if npdata.shape[2] == 2:
                return DataType.FLOW
            elif npdata.shape[2] == 3 or npdata.shape[2] == 4:
                return DataType.COLOR
            else:
                return DataType.MULTICHANNEL
        else:
            raise ValueError('Input data with ndim > 3 (i.e. %d) is not supported!' % npdata.ndim)
    
    @staticmethod
    def fromFilename(filename):
        """
        Returns the best guess on the proper data type given the filename.
        In particular, we check the extension and return:
        * *.flo files: DataType.FLOW
        * *.npy files: DataType.MULTICHANNEL
        * Image files will be opened with default settings and are either DataType.MONOCHROME or .COLOR
        Raises a ValueError if the file extension is not a supported image extension.
        """
        _, ext = os.path.splitext(filename.lower())
        if ext == '.flo':
            return DataType.FLOW
        elif ext == '.npy':
            return DataType.MULTICHANNEL
        else:
            try:
                data = imutils.imread(filename)
                if data.ndim < 3 or data.shape[2] == 1:
                    return DataType.MONOCHROME
                return DataType.COLOR
            except UnidentifiedImageError:
                raise ValueError('Filename is not a loadable image.')
        return DataType.COLOR

    @staticmethod
    def pilModeFor(data_type, data=None):
        """
        Returns PIL's conversion mode for the corresponding data_type.
        Returns None for data which cannot be handled by PIL, i.e.: optical
        flow and multi-channel data.
        If available, provide the data too - so we can tell RGB from RGBA if
        data_type indicates a COLOR image.

        See also PIL modes:
        https://pillow.readthedocs.io/en/3.1.x/handbook/concepts.html#concept-modes
        """
        if data_type == DataType.COLOR:
            # Data may be single-channel, but the user requested us to treat
            # it like a RGB image.
            if data is None or len(data.shape) < 3 or data.shape[2] < 4:
                return 'RGB'
            else:
                return 'RGBA'
        elif data_type == DataType.MONOCHROME:
            return 'L'
        elif data_type == DataType.CATEGORICAL:
            return 'I'
        elif data_type == DataType.BOOL:
            return '1'
        elif data_type == DataType.DEPTH:
            return 'I'
        elif data_type in [DataType.FLOW, DataType.MULTICHANNEL]:
            return None
        else:
            raise NotImplementedError('PIL mode for DataType "%s" is not yet configured' % DataType.toStr(data_type))


class InspectionWidget(QWidget):
    """Widget to display a single image."""

    # Identifiers for visualization drop down
    VIS_RAW = -1
    # Ensure that grayscale is the second option
    VIS_COLORMAPS = ['Grayscale'] + [cmn for cmn in colormaps.colormap_names if cmn.lower() != 'grayscale']

    # Emitted whenever the user changes the image scale (float).
    # The integer parameter will hold the "inspector_id" as set
    # upon __init__().
    imgScaleChanged = Signal(int, float)

    # Notify observers that a new image has been loaded
    fileOpened = Signal(int)

    # Emitted whenever the user moves the mouse across the image
    # Yields the "inspector_id" and corresponding (image) pixel position
    # as QPointF or None.
    # If the position is None, this indicates that the user simply changed
    # the visualization mode (e.g. switching from grayscale to raw data)
    # and thus, the currently displayed tooltip (if any) must be updated.
    showTooltipRequest = Signal(int, object)

    def __init__(
            self,
            inspector_id, data, data_type,
            display_settings=None,
            categorical_labels=None):
        super(InspectionWidget, self).__init__()
        # ID to distinguish signals from different inspectors (used when displaying multiple images)
        self._inspector_id = inspector_id
        # Input/raw data
        self._data = None
        # Type (e.g. user can decide to show a monochrome image as categorical input)
        self._data_type = None
        # Whether input data is a single- or multi-channel image
        self._is_single_channel = False
        # Currently visualized data (e.g. a single channel)
        self._visualized_data = None
        # Currently visualized pseudocolorized data
        self._visualized_pseudocolor = None
        # Whether the image viewer should be reset (adjust size and translation)
        self._reset_viewer = True
        # Function handle to format data values
        self.__fmt_fx = None
        # Category labels to be displayed if data is CATEGORICAL
        self._categorical_labels = None
        # Handles to file I/O dialogs
        self._save_file_dialog = None
        self._open_file_dialog = None
        self._reload_visualization_dialog = None
        # Now, show the given data:
        self.inspectData(data, data_type, display_settings, categorical_labels)

    def getData(self):
        return self._data

    def getDataType(self):
        return self._data_type

    def inspectData(self, data, data_type=None, display_settings=None, categorical_labels=None):
        """
        Adjust the widget to show the given input data.

        data:           numpy.array to be visualized
        data_type:      Enum DataType or None (will be guessed from data via
                        DataType.fromData())
        display_settings:   If you have want to restore display settings, e.g.
                        selected colormap, zoom/scroll settings, provide this
                        parameter. Can be obtained via currentDisplaySettings().
        """
        self._data = data
        if data is not None:
            self._data_type = DataType.fromData(data) if data_type is None else data_type
            self._is_single_channel = (data.ndim < 3) or (data.shape[2] == 1)
        self._visualized_data = None
        self._visualized_pseudocolor = None
        self._categorical_labels = categorical_labels
        self._reset_viewer = True
        # Set up GUI
        self.__resetLayout()
        # Analyze the given data (range, data type, channels, etc.)
        self.__prepareDataStatistics()
        # Now we're ready to visualize the data ...
        self.__updateDisplay()
        # ... and potentially restore display settings
        self.restoreDisplaySettings(display_settings)

    def setImageScaleAbsolute(self, scale):
        """Adjust the image scale (float)."""
        self._img_viewer.setScale(scale)
        self.update()

    def setImageScaleFit(self):
        self._img_viewer.scaleToFitWindow()
        self.update()

    def imageScale(self):
        return self._img_viewer.scale()

    def currentDisplaySettings(self):
        settings = {
            'dd-visualization': self._visualization_dropdown.get_input()[0],
            'data-type': self._data_type,
            'rs-limits': (self._visualization_range_slider.get_input(), self._visualization_range_slider.get_range()),
            'categorical-labels': self._categorical_labels
        }
        if not self._is_single_channel:
            settings['dd-selected-layer'] = self._layer_dropdown.get_input()[0]
            settings['cb-same-limits'] = self._checkbox_global_limits.get_input()
        # Extend dictionary by the image viewer's settings
        settings.update(self._img_viewer.currentDisplaySettings())
        return settings

    def restoreDisplaySettings(self, settings):
        if settings is None:
            return
        # Restore customized UI settings only if data type didn't change.
        if self._data_type == settings['data-type']:
            self._visualization_dropdown.set_value(settings['dd-visualization'])
            rss_values, rss_range = settings['rs-limits']
            self._visualization_range_slider.set_range(rss_range[0], rss_range[1])
            self._visualization_range_slider.set_value(rss_values)
            if not self._is_single_channel:
                self._layer_dropdown.set_value(settings['dd-selected-layer'])
                self._checkbox_global_limits.set_value(settings['cb-same-limits'])
            # Restore custom category labels (unless the user already set labels)
            if self._categorical_labels is None:
                self._categorical_labels = settings['categorical-labels']
                self._colorbar.setCategoricalLabels(self._categorical_labels)
        # Restore zoom/translation settings
        self._img_viewer.restoreDisplaySettings(settings)
        self.__updateDisplay()

    def pixelFromGlobal(self, global_pos):
        """
        Map a global position, e.g. QCursor.pos(), to the corresponding
        pixel location.
        """
        return self._img_viewer.pixelFromGlobal(global_pos)

    def getPixelValue(self, px_x, px_y):
        """Retrieves the image data at location (px_x, px_y)."""
        if self._data is None:
            return None
        x = int(px_x)
        y = int(px_y)
        width = self._data.shape[1] if self._data.ndim > 1 else 1
        if x < 0 or x >= width or y < 0 or y >= self._data.shape[0]:
            return None
        query = dict()
        query['pos'] = '({:d}, {:d})'.format(x, y)

        # Representation of raw data
        query['currlayer'] = None
        if self._is_single_channel:
            value = self._data[y] if self._data.ndim == 1 else self._data[y, x]
            if self._data_type == DataType.CATEGORICAL \
                    and self._categorical_labels is not None \
                    and value in self._categorical_labels:
                query['rawstr'] = self._categorical_labels[value] + ' (' + self.__fmt_fx(value) + ')'
            else:
                query['rawstr'] = self.__fmt_fx(value)
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
        query['dtypestr'] = 'Category' if self._data_type == DataType.CATEGORICAL \
            else ('Flow' if self._data_type == DataType.FLOW else 'Raw data')

        if self._visualized_pseudocolor is None:
            query['pseudocol'] = None
        else:
            query['pseudocol'] = '[' + ', '.join(
                ['{:d}'.format(self._visualized_pseudocolor[y, x, c])
                    for c in range(self._visualized_pseudocolor.shape[2])]) \
                    + ']'

        query['scale'] = self.imageScale()
        return query

    def linkAxes(self, other_inspection_widgets):
        self._img_viewer.linkViewers([oiw._img_viewer for oiw in other_inspection_widgets])

    def clearLinkedAxes(self):
        self._img_viewer.clearLinkedViewers()

    def zoomImage(self, delta):
        self._img_viewer.zoom(delta)

    def scrollImage(self, delta, orientation):
        self._img_viewer.scroll(delta, orientation)

    @Slot()
    def showFileSaveDialog(self):
        thumbnails = {
            inspection_widgets.SaveInspectionFileDialog.SAVE_VISUALIZATION: self._img_viewer.imagePixmap(),
            inspection_widgets.SaveInspectionFileDialog.SAVE_RAW: inspection_utils.pixmapFromNumPy(self._data)
        }
        self._save_file_dialog = inspection_widgets.SaveInspectionFileDialog(
            self._data_type, thumbnails=thumbnails, parent=self)
        self._save_file_dialog.finished.connect(self.__onSaveFinished)
        self._save_file_dialog.open()

    @Slot()
    def showFileOpenDialog(self):
        # self._open_file_dialog = OpenInspectionFileDialog(self._data_type, parent=self)
        self._open_file_dialog = inspection_widgets.OpenInspectionFileDialog(
            data_type=self._data_type,
            thumbnail=self._img_viewer.imagePixmap(),
            parent=self)
        self._open_file_dialog.finished.connect(self.__onOpenFinished)
        self._open_file_dialog.open()

    @Slot()
    def __onSaveFinished(self):
        res = self._save_file_dialog.getSelection()
        if res is None or any([r is None for r in res]):
            return
        filename, save_type = res
        if save_type == inspection_widgets.SaveInspectionFileDialog.SAVE_VISUALIZATION:
            filename = inspection_utils.FilenameUtils.ensureImageExtension(filename)
            pc = self._visualized_pseudocolor
            save_data = self._visualized_data if pc is None else pc
            save_fx = imutils.imsave
        elif save_type == inspection_widgets.SaveInspectionFileDialog.SAVE_RAW:
            if self._data_type == DataType.FLOW:
                filename = inspection_utils.FilenameUtils.ensureFlowExtension(filename)
                save_fx = flowutils.flosave
            elif self._data_type == DataType.MULTICHANNEL:
                filename = inspection_utils.FilenameUtils.ensureNumpyExtension(filename)
                save_fx = np.save
            else:
                filename = inspection_utils.FilenameUtils.ensureImageExtension(filename)
                save_fx = imutils.imsave
            save_data = self._data
        else:
            raise NotImplementedError('Save as %d type is not yet supported' % save_type)

        try:
            # Successfully (manually) tested:
            # * Save raw input:
            #   o Save RGB (png, jpg)
            #     + Load RGB as RGB, save RGB
            #     + Load mono as RGB, save RGB
            #   o Save mono (png, jpg)
            #     + Load mono as mono, save mono
            #     + Load RGB as mono, save mono
            #   o Save depth (16bit png)
            #     + Load depth as depth, save depth
            #     + Load mono as depth, save depth
            #     + Load RGB as depth, save depth
            #   o Save boolean mask (1bit png)
            # * Save visualization ==> RGB png/jpg
            # * Save optical flow (raw & visualization)
            #
            # Nice-to-have: automated tests (see tests of vito package on how
            # to check file metadata)
            save_fx(filename, save_data)
        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText('Error saving {:s}'.format(
                'current visualization' if save_type == inspection_widgets.SaveInspectionFileDialog.SAVE_VISUALIZATION
                else 'raw input data'))
            msg.setInformativeText('Logged exception:\n{:s}'.format(str(e)))
            msg.setWindowTitle('Error')
            msg.exec()

    @Slot(str)
    def __openDroppedFilename(self, filename):
        if filename is None:
            return
        # 1) Guess datatype
        try:
            dtype = DataType.fromFilename(filename)
        except ValueError:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText('{:s} is not a supported image file.'.format(filename))
            msg.setWindowTitle('Error')
            msg.exec()
            return
        # 2) Initialize open dialog (pre-set filename and datatype)
        self._open_file_dialog = inspection_widgets.OpenInspectionFileDialog(
            data_type=dtype,
            thumbnail=None if self._data is None else self._img_viewer.imagePixmap(),
            filename_suggestion=filename,
            parent=self)
        self._open_file_dialog.finished.connect(self.__onOpenFinished)
        self._open_file_dialog.open()

    @Slot()
    def __onOpenFinished(self):
        res = self._open_file_dialog.getSelection()
        if res is None or any([r is None for r in res]):
            return
        try:
            filename, data_type = res
            if data_type == DataType.FLOW:
                data = flowutils.floread(filename)
            elif data_type == DataType.MULTICHANNEL:
                data = np.load(filename)
            else:
                data = imutils.imread(filename, mode=DataType.pilModeFor(data_type, data=None))
                if data_type == DataType.BOOL:
                    data = data.astype(np.bool)
            current_display = self.currentDisplaySettings()
            self.inspectData(data, data_type, display_settings=current_display)
            # Notify observers of loaded data
            self.fileOpened.emit(self._inspector_id)
        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText('Error loading file as type "{:s}"'.format(
                DataType.toStr(data_type)))
            msg.setInformativeText('Logged exception:\n{:s}'.format(str(e)))
            msg.setWindowTitle('Error')
            msg.exec()

    @Slot()
    def showVisualizationChangeDialog(self):
        self._reload_visualization_dialog = inspection_widgets.ChangeDataTypeDialog(
            self._data_type, self._img_viewer.imagePixmap(), parent=self)
        self._reload_visualization_dialog.finished.connect(self.__onReloadDialogFinished)
        self._reload_visualization_dialog.open()

    @Slot()
    def __onReloadDialogFinished(self):
        new_data_type = self._reload_visualization_dialog.getSelection()
        if new_data_type is None:
            return
        if new_data_type == self._data_type:
            print('The same data type has been selected. Reload request will be ignored.')
            return
        try:
            reload_data = self._data
            if self._data_type == DataType.BOOL:
                if new_data_type in [DataType.COLOR, DataType.MONOCHROME]:
                    reload_data = self._data.astype(np.uint8)
                elif new_data_type == DataType.CATEGORICAL:
                    reload_data = self._data.astype(np.int32)
                elif new_data_type in [DataType.FLOW, DataType.DEPTH, DataType.MULTICHANNEL]:
                    reload_data = self._data.astype(np.float32)
                else:
                    raise NotImplementedError("Reloading Boolean as '{}' is not yet supported.".format(new_data_type.toStr()))
            self.inspectData(reload_data, new_data_type)
            # Notify observers of loaded data
            self.fileOpened.emit(self._inspector_id)
        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText('Error reloading data as type "{:s}"'.format(
                DataType.toStr(new_data_type)))
            msg.setInformativeText('Logged exception:\n{:s}'.format(str(e)))
            msg.setWindowTitle('Error')
            msg.exec()

    def __prepareDataStatistics(self):
        """
        Analyzes the internal _data field (range, data type, channels,
        etc.) and sets member variables accordingly.
        Additionally, information will be printed to stdout and shown on
        the GUI.
        """
        contains_nan = np.any(np.isnan(self._data))
        contains_inf = np.any(np.isinf(self._data))
        if contains_nan or contains_inf:
            # Prepare output string
            nonfin_str = ''
            if contains_inf:
                nonfin_str += 'Inf'
            if contains_nan:
                if len(nonfin_str) > 0:
                    nonfin_str += ', '
                nonfin_str += 'NaN'
            # Compute limits on finite data only
            finite_data = self._data[np.isfinite(self._data)]
        else:
            finite_data = self._data
        self._data_limits = [np.min(finite_data[:]), np.max(finite_data[:])]
        # self._data_limits = [np.min(self._data[:]), np.max(self._data[:])]

        # Prepare 'header' for stdout summary
        stdout_str = list()
        stdout_str.append('##################################################')
        stdout_str.append('Data inspection widget [{:d}]:\n'.format(self._inspector_id))
        if contains_inf or contains_nan:
            stdout_str.append('!! Data contains non-finite values: {}'.format(nonfin_str))
            stdout_str.append('   These values will be ignored for the following statistics !!\n')
        stdout_str.append('Data type: {} ({})'.format(
            self._data.dtype, DataType.toStr(self._data_type)))
        stdout_str.append('Shape:     {}\n'.format(self._data.shape))

        # Prepare label for GUI summary
        lbl_txt = '<table cellpadding="5">'
        if contains_inf or contains_nan:
            lbl_txt += '<tr><td colspan="2"><font color="red"><b>Contains non-finite values: {:s}</b></font></td></tr>'.format(
                nonfin_str)
            lbl_txt += '<tr><td colspan="2">Non-finite values are ignored for these statistics!</td></tr>'
        lbl_txt += '<tr><td><b>Type:</b> {} ({})</td><td><b>Shape:</b> {}</td></tr>'.format(
            self._data.dtype, DataType.toStr(self._data_type), self._data.shape)

        if self._data_type == DataType.BOOL:
            self._data_limits = [float(v) for v in self._data_limits]
            self.__fmt_fx = inspection_utils.fmtb
            self._colorbar.setBoolean(True)
            self._visualization_range_slider.set_range(0, 1)
            self._visualization_range_slider.setEnabled(False)
        elif self._data_type == DataType.CATEGORICAL:
            self.__fmt_fx = inspection_utils.fmti
            data_cats, inv_cats = np.unique(self._data, return_inverse=True)
            if self._categorical_labels is None:
                self._data_categories = data_cats
                self._data_inverse_categories = inv_cats.reshape(self._data.shape)
                num_present_categories = -1
            else:
                # Gather all categories provided by the user
                self._data_categories = [k for k in self._categorical_labels]
                # Get type of categories (needed to cast the numpy values below to perform the
                # category lookup and to check for missing categories)
                dctype = type(self._data_categories[0])
                # Check if the user forgot any categories
                num_present_categories = len(data_cats)
                missing_cats = [dctype(k) for k in data_cats if dctype(k) not in self._data_categories]
                if len(missing_cats) > 0:
                    print("\n[W] Not all categories are contained in the provided 'categorical_labels'!")
                    print('    Missing categories: ', missing_cats, '\n')
                    self._data_categories.extend(missing_cats)
                lookup = {k: self._data_categories.index(k) for k in self._data_categories}
                ic = np.array([lookup[dctype(val)] for val in np.nditer(self._data)])
                self._data_inverse_categories = ic.reshape(self._data.shape)

            self._colorbar.setCategories(self._data_categories)
            self._colorbar.setCategoricalLabels(self._categorical_labels)
            self._visualization_range_slider.set_range(0, len(self._data_categories) - 1)
        else:
            self.__fmt_fx = inspection_utils.bestFormatFx(self._data_limits)

        # Prepare QLabel and stdout message:
        if self._data_type == DataType.BOOL:
            lbl_txt += '<tr><td colspan="2"><b>Binary mask.</b></td></tr>'
        elif self._data_type == DataType.CATEGORICAL:
            if num_present_categories < 0:
                stdout_str.append('Label image with {:d} categories'.format(
                    len(self._data_categories)))
                lbl_txt += '<tr><td colspan="2"><b>Label image, {:d} classes.</b></td></tr>'.format(
                    len(self._data_categories))
            else:
                stdout_str.append('Label image with {:d}/{:d} categories'.format(
                    num_present_categories, len(self._data_categories)))
                lbl_txt += '<tr><td colspan="2"><b>Label image, {:d}/{:d} classes.</b></td></tr>'.format(
                    num_present_categories, len(self._data_categories))
        else:
            # global_mean = np.mean(self._data[:])
            # global_std = np.std(self._data[:])
            global_mean = np.mean(finite_data[:])
            global_std = np.std(finite_data[:])
            self._visualization_range_slider.set_range(0, 255)

            stdout_str.append('Minimum: {}'.format(self._data_limits[0]))
            stdout_str.append('Maximum: {}'.format(self._data_limits[1]))
            stdout_str.append('Mean:    {} +/- {}\n'.format(global_mean, global_std))

            lbl_txt += '<tr><td><b>Range:</b> [{}, {}]</td><td><b>Mean:</b> {} &#177; {}</td></tr>'.format(
                self.__fmt_fx(self._data_limits[0]),
                self.__fmt_fx(self._data_limits[1]),
                self.__fmt_fx(global_mean),
                self.__fmt_fx(global_std))

            if not self._is_single_channel:
                for c in range(self._data.shape[2]):
                    layer_data = self._data[:, :, c]
                    is_finite = np.isfinite(layer_data)
                    finite_layer_data = layer_data[is_finite]
                    # cmin = np.min(self._data[:, :, c])
                    # cmax = np.max(self._data[:, :, c])
                    # cmean = np.mean(self._data[:, :, c])
                    # cstd = np.std(self._data[:, :, c])
                    cmin = np.min(finite_layer_data)
                    cmax = np.max(finite_layer_data)
                    cmean = np.mean(finite_layer_data)
                    cstd = np.std(finite_layer_data)

                    if not np.all(is_finite):
                        stdout_str.append('!! Channel {} contains non-finite values !!'.format(c))
                    stdout_str.append('Minimum on channel {}: {}'.format(c, cmin))
                    stdout_str.append('Maximum on channel {}: {}'.format(c, cmax))
                    stdout_str.append('Mean on channel {}:    {} +/- {}\n'.format(c, cmean, cstd))

                    lbl_txt += '<tr><td>Channel {} range: [{}, {}]</td><td>Mean: {} &#177; {}</td></tr>'.format(
                        c, self.__fmt_fx(cmin), self.__fmt_fx(cmax), self.__fmt_fx(cmean), self.__fmt_fx(cstd))
        # Print to stdout
        for s in stdout_str:
            print(s)
        # Show on label
        lbl_txt += '</table>'
        self._data_label.setText(lbl_txt)
        self._data_label.update()
        # Now we can properly format values of the range slider, too
        self._visualization_range_slider.set_value_format_fx(self.__formatRangeSliderValue)

    def __resetLayout(self):
        # Add a file I/O widget to open/save an image from this
        # inspection widget:
        file_io_widget = inspection_widgets.ToolbarFileIOWidget(
            vertical=True, icon_size=QSize(24, 24))
        file_io_widget.fileSaveRequest.connect(self.showFileSaveDialog)
        file_io_widget.fileOpenRequest.connect(self.showFileOpenDialog)
        file_io_widget.visualizationChangeRequest.connect(self.showVisualizationChangeDialog)

        input_layout = QVBoxLayout()
        # Let user select a single channel if multi-channel input is provided
        if not self._is_single_channel:
            if self._data_type == DataType.FLOW and self._data.shape[2] == 2:
                dd_options = [(-1, 'All'), (0, 'Horizontal'), (1, 'Vertical')]
            else:
                dd_options = [(-1, 'All')] + [(c, 'Layer {:d}'.format(c)) for c in range(self._data.shape[2])]
            self._layer_dropdown = inputs.DropDownSelectionWidget('Select layer:', dd_options)
            self._layer_dropdown.value_changed.connect(self.__updateDisplay)
            self._layer_dropdown.value_changed.connect(lambda: self.showTooltipRequest.emit(self._inspector_id, None))
            self._layer_dropdown.setToolTip('Select which layer to visualize')
            input_layout.addWidget(self._layer_dropdown)

        if self._is_single_channel or self._data_type == DataType.CATEGORICAL:
            self._checkbox_global_limits = None
        else:
            self._checkbox_global_limits = inputs.CheckBoxWidget(
                'Same limits across channels:',
                checkbox_left=False, is_checked=True)
            self._checkbox_global_limits.value_changed.connect(self.__updateDisplay)
            self._checkbox_global_limits.value_changed.connect(lambda: self.showTooltipRequest.emit(self._inspector_id, None))
            self._checkbox_global_limits.setToolTip(
                'If <b>checked</b>, visualization uses <b>min/max</b> from <tt>data[:]</tt> instead of <tt>data[:, :, channel]</tt>')
            input_layout.addWidget(self._checkbox_global_limits)

        # Let user select the visualization method
        vis_options = [(InspectionWidget.VIS_RAW, 'Raw data'), (0, 'Grayscale')] + \
            [(i, 'Pseudocolor {:s}'.format(InspectionWidget.VIS_COLORMAPS[i]))
                for i in range(1, len(InspectionWidget.VIS_COLORMAPS))]
        # Select viridis colormap by default (note missing "-1", because we
        # prepend the "raw" option) for single channel. Default to turbo for optical flow.
        # Otherwise, just visualize the raw data by default.
        self._visualization_dropdown = inputs.DropDownSelectionWidget('Visualization:', vis_options,
            initial_selected_index=len(InspectionWidget.VIS_COLORMAPS) if self._is_single_channel
                else (len(InspectionWidget.VIS_COLORMAPS)-1 if self._data_type == DataType.FLOW else 0))
        self._visualization_dropdown.value_changed.connect(self.__updateDisplay)
        self._visualization_dropdown.value_changed.connect(lambda: self.showTooltipRequest.emit(self._inspector_id, None))
        self._visualization_dropdown.setToolTip('Select raw vs. colorized')
        input_layout.addWidget(self._visualization_dropdown)

        self._visualization_range_slider = inputs.RangeSliderSelectionWidget('Shown limits:',
            min_value=0, max_value=255,
            value_format_fx=None, allow_text_input=False)
        self._visualization_range_slider.value_changed.connect(self.__updateDisplay)
        self._visualization_range_slider.value_changed.connect(lambda: self.showTooltipRequest.emit(self._inspector_id, None))
        self._visualization_range_slider.setToolTip('Adjust visualization limits')
        input_layout.addWidget(self._visualization_range_slider)

        # Image viewer and colorbar
        img_layout = QHBoxLayout()
        self._img_viewer = imgview.ImageViewer()
        self._img_viewer.mouseMoved.connect(lambda px: self.showTooltipRequest.emit(self._inspector_id, px))
        self._img_viewer.viewChanged.connect(lambda: self.showTooltipRequest.emit(self._inspector_id, None))
        self._img_viewer.imgScaleChanged.connect(lambda s: self.imgScaleChanged.emit(self._inspector_id, s))
        self._img_viewer.filenameDropped.connect(self.__openDroppedFilename)
        self._img_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        img_layout.addWidget(self._img_viewer)

        self._colorbar = inspection_widgets.ColorBar()
        self._colorbar.setToolTip('Color bar')
        img_layout.addWidget(self._colorbar)

        # Label to show important image statistics/information
        # self._data_label_scroll_area.setWidgetResizable(True)
        self._data_label = QLabel()
        self._data_label.setFrameShape(QFrame.Panel)
        self._data_label.setFrameShadow(QFrame.Sunken)
        self._data_label.setToolTip('Data properties')
        # The info label will be placed in a scroll area, in case it is too large
        self._data_label_scroll_area = QScrollArea()
        self._data_label_scroll_area.setWidget(self._data_label)
        self._data_label_scroll_area.setWidgetResizable(True)
        self._data_label_scroll_area.setMaximumHeight(100)

        # The "menu"/"control bar" inputs/controls looks like:
        #   File I/O  |  Visualization  | Image Information.
        top_row_layout = QHBoxLayout()
        top_row_layout.addWidget(file_io_widget)
        top_row_layout.addWidget(inputs.VLine())
        # Make a dummy widget holding all user input controls, so we can force
        # a maximum size.
        input_layout.setAlignment(Qt.AlignTop)
        # top_row_layout.addLayout(input_layout)
        self._input_widget = QWidget()
        self._input_widget.setLayout(input_layout)
        top_row_layout.addWidget(self._input_widget)
        top_row_layout.addWidget(self._data_label_scroll_area)
        top_row_layout.setContentsMargins(0, 0, 0, 0)
        # Set the main widget's layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_row_layout)
        main_layout.addLayout(img_layout)
        # Set just a small margin around the widget
        main_layout.setContentsMargins(5, 5, 5, 5)
        # Set font of tool tips
        QToolTip.setFont(QFont('SansSerif', 10))
        # Reparent layout to temporary object (so we can replace it)
        if self.layout() is not None:
            QWidget().setLayout(self.layout())
        self.setLayout(main_layout)

    def resizeEvent(self, event):
        # Upon initialization, we didn't know the dimension of the input
        # widgets. Now, we can set a size constraint for inputs and the
        # data information label.
        min_input_height = self._input_widget.layout().minimumSize().height()
        self._data_label_scroll_area.setMaximumHeight(min_input_height)
        self._input_widget.setMaximumHeight(min_input_height)
        return super(InspectionWidget, self).resizeEvent(event)

    @Slot()
    def __updateDisplay(self):
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
            # Disable the range slider for boolean, categorical and RAW data
            disable_range_slider = self._data_type in [DataType.BOOL, DataType.CATEGORICAL] \
                or self._visualization_dropdown.get_input()[0] == InspectionWidget.VIS_RAW
            self._visualization_range_slider.setEnabled(not disable_range_slider)
        else:
            self._visualization_dropdown.setEnabled(False)
            self._visualization_range_slider.setEnabled(False)

        # Select visualization mode
        vis_selection = self._visualization_dropdown.get_input()[0]
        if vis_selection == InspectionWidget.VIS_RAW or not is_single_channel:
            if not is_single_channel and self._data_type == DataType.FLOW:
                self._visualized_pseudocolor = flowutils.colorize_flow(self._visualized_data)
                self._img_viewer.showImage(self._visualized_pseudocolor, reset_scale=self._reset_viewer)
                self._colorbar.setFlowWheel(True)
                self._colorbar.setVisible(True)
                self._colorbar.update()
            else:
                self._img_viewer.showImage(self._visualized_data, reset_scale=self._reset_viewer)
                self._colorbar.setVisible(False)
                self._visualized_pseudocolor = None
        else:
            cm = colormaps.by_name(InspectionWidget.VIS_COLORMAPS[vis_selection])
            if self._visualization_range_slider.isEnabled():
                # Query range slider for the visualization limits
                limits = self.__getRangeSliderValues()
                self._colorbar.setLimits(limits)
                pc = imvis.pseudocolor(self._visualized_data, color_map=cm, limits=limits)
            else:
                # Categorical and boolean data requires special treatment:
                if self._data_type == DataType.CATEGORICAL:
                    pc = imvis.pseudocolor(self._data_inverse_categories,
                        color_map=cm, limits=[0, len(self._data_categories)-1])
                else:
                    limits = [np.min(self._visualized_data[:]), np.max(self._visualized_data[:])]
                    if self._data.dtype is np.dtype('bool'):
                        limits = [float(v) for v in limits]
                    self._colorbar.setLimits(limits)
                    pc = imvis.pseudocolor(self._visualized_data, color_map=cm, limits=limits)
            self._visualized_pseudocolor = pc
            self._img_viewer.showImage(pc, reset_scale=self._reset_viewer)
            self._colorbar.setColormap(cm)
            self._colorbar.setFlowWheel(False)
            self._colorbar.setVisible(True)
            self._colorbar.update()
            # We need to update the range slider's label text whenever there's a layer change
            # or the "global limits" checkbox is toggled. However, these already cause a
            # __updateDisplay() call. Thus, we just need to reset the label formatting function:
            self._visualization_range_slider.set_value_format_fx(self.__formatRangeSliderValue)
        self._reset_viewer = False

    def __getRangeSliderValues(self):
        lower, upper = self._visualization_range_slider.get_input()
        lower = self.__rangeSliderValueToDataRange(lower)
        upper = self.__rangeSliderValueToDataRange(upper)
        return (lower, upper)

    def __rangeSliderValueToDataRange(self, value):
        # TODO should we raise an error for categorical/boolean data?
        if self._data_type == DataType.CATEGORICAL:
            return self._data_categories[max(0, min(len(self._data_categories)-1, value))]
        else:
            # Otherwise, the range slider has been set to [0, 255] or [0, 1]
            slider_interval = 1 if self._data_type == DataType.BOOL else 255
            if self._visualized_data is None or (self._checkbox_global_limits is not None
                    and self._checkbox_global_limits.get_input()):
                limits = self._data_limits
            else:
                limits = [np.min(self._visualized_data[:]), np.max(self._visualized_data[:])]
                if self._data.dtype is np.dtype('bool'):
                    limits = [float(v) for v in limits]
            data_interval = limits[1] - limits[0]
            return value / slider_interval * data_interval + limits[0]

    def __formatRangeSliderValue(self, value):
        return self.__fmt_fx(self.__rangeSliderValueToDataRange(value))


class Inspector(QMainWindow):
    """Main window to inspect the given data"""

    @staticmethod
    def makeWindowTitle(label, data, data_type):
        # If there's a user-defined label, use this:
        if label is not None:
            return label
        if data is None:
            return 'Data Inspection'
        # If we show multiple images, show [multi]:
        if inspection_utils.isArrayLike(data):
            return 'Data Inspection [multiple viewers]'
        # Otherwise, use the given data_type (or compute it from data if None)
        if data_type is None:
            data_type = DataType.fromData(data)
        return 'Data Inspection [{}]'.format(DataType.toStr(data_type))

    def __init__(
            self, data, data_type, display_settings=None,
            max_num_widgets_per_row=3,
            initial_window_size=QSize(1280, 720),
            window_title=None,
            force_linked_viewers=False,
            categorical_labels=None):
        super(Inspector, self).__init__()
        self._initial_window_size = initial_window_size
        self._user_defined_window_title = window_title
        self._should_link_viewers = False
        self._display_tooltip = True
        self._open_file_dialog = None
        self._save_file_dialog = None
        # Create the central widget (layout will be adjusted within
        # inspectData()
        self._main_widget = QWidget()
        self.setCentralWidget(self._main_widget)
        # Set icon
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'iminspect_assets', 'iminspect.svg')))
        # Set up keyboard shortcuts
        self.__addShortcuts()
        # Add a zoom widget (scale original, fit window, ...) to the status bar
        self._zoom_widget = inspection_widgets.ToolbarZoomWidget(self.centralWidget())
        self._zoom_widget.zoomBestFitRequest.connect(self.scaleImagesFit)
        self._zoom_widget.zoomOriginalSizeRequest.connect(self.scaleImagesOriginal)
        self.statusBar().addPermanentWidget(self._zoom_widget)
        # Finally, show the given data
        self._inspectors = list()
        self.inspectData(data, data_type,
            max_num_widgets_per_row=max_num_widgets_per_row,
            display_settings=display_settings,
            force_linked_viewers=force_linked_viewers,
            categorical_labels=categorical_labels)
        if initial_window_size is not None:
            self.resize(initial_window_size)

    def inspectData(
            self, data, data_type,
            max_num_widgets_per_row=3, display_settings=None,
            force_linked_viewers=False,
            categorical_labels=None):
        """
        Loads the given data and resets the widget's layout.
        See inspector.inspect() for documentation of the parameters.
        """
        if data is None:
            sz = (640, 320)
            if self._initial_window_size is not None:
                sz = (self._initial_window_size.width(), self._initial_window_size.height())
            data = inspection_utils.emptyInspectionImage(sz)

        if inspection_utils.isArrayLike(data):
            # Check if all images have the same width/height.
            matching_input_shape = True
            # Place inspection widgets in a grid layout.
            layout = QGridLayout()
            # Create inspection widgets:
            num_inputs = len(data)
            self._inspectors = list()
            for idx in range(num_inputs):
                dt = data_type[idx] if inspection_utils.isArrayLike(data_type) else data_type
                clbl = categorical_labels[idx] if inspection_utils.isArrayLike(categorical_labels) else categorical_labels
                insp = InspectionWidget(idx, data[idx], dt,
                    display_settings=None
                        if display_settings is None or display_settings['num-inspectors'] != num_inputs
                        else display_settings['inspection-widgets'][idx],
                        categorical_labels=clbl)
                self._inspectors.append(insp)
                layout.addWidget(insp,
                    idx // max_num_widgets_per_row, idx % max_num_widgets_per_row)
                if data[idx].shape[0] != data[0].shape[0] \
                    or (data[idx].ndim > 1 and data[0].ndim > 1 and data[idx].shape[1] != data[0].shape[1]):
                    matching_input_shape = False
            # Turn off scale display if images have different resolution
            self._zoom_widget.showScaleLabel(matching_input_shape)
            # Link image viewers if images have the same resolution
            if matching_input_shape or force_linked_viewers:
                self._should_link_viewers = True
                self.__linkInspectors()
        else:
            # Single image to show, so we only need a single inspection widget
            insp = InspectionWidget(0, data, data_type,
                display_settings=None
                    if display_settings is None or display_settings['num-inspectors'] != 1
                    else display_settings['inspection-widgets'][0],
                categorical_labels=categorical_labels)
            self._inspectors = [insp]
            layout = QHBoxLayout()
            layout.addWidget(insp)
            self._zoom_widget.showScaleLabel(True)
            self._should_link_viewers = False

        # Important to prevent ugly gaps between status bar and image canvas:
        margins = layout.contentsMargins()
        layout.setContentsMargins(margins.left(), margins.top(), margins.right(), 0)
        self._main_widget.setLayout(layout)

        for insp in self._inspectors:
            insp.fileOpened.connect(self.__fileHasBeenOpened)
            insp.showTooltipRequest.connect(self.showPixelValue)
            # Note that the scale label of the zoom widget has already been
            # disabled/hidden (if there are multiple inputs and sizes differ).
            # Thus, we can connect the imgScaleChanged widget here anyways:
            insp.imgScaleChanged.connect(lambda _, s: self._zoom_widget.setScale(s))
            # We also need to display the initial scale value:
            self._zoom_widget.setScale(insp.imageScale())

        # Restore display settings
        self.restoreDisplaySettings(display_settings)

    def currentDisplaySettings(self):
        """
        Returns a dictionary of currently applied UI settings/attributes.
        This can be used to restore these settings after opening/displaying
        subsequent data via restoreDisplaySettings().
        """
        settings = {
            'win-size': self.size(),
            'win-pos': self.mapToGlobal(QPoint(0, 0)),
            'num-inspectors': len(self._inspectors)
        }
        inspection_widgets_settings = [insp.currentDisplaySettings() for insp in self._inspectors]
        settings['inspection-widgets'] = inspection_widgets_settings
        return settings

    def restoreDisplaySettings(self, settings):
        """
        Re-applies the display settings previously obtained via
        currentDisplaySettings() where applicable. This means that if the
        data type changed in between, type-specific UI settings/attributes
        will not be restored.
        """
        if settings is None:
            return
        if 'win-size' in settings:
            self.resize(settings['win-size'])
        # Note that restoring the position doesn't always work (issues with
        # windows that are placed partially outside the screen)
        if 'win-pos' in settings:
            self.move(settings['win-pos'])
        # Restore each viewer-specific display only if the number of viewers
        # stayed the same:
        num_inspectors = len(self._inspectors)
        if 'num-inspectors' in settings and num_inspectors == settings['num-inspectors']:
            for idx in range(num_inspectors):
                self._inspectors[idx].restoreDisplaySettings(settings['inspection-widgets'][idx])
        self.update()

    def __linkInspectors(self):
        """Link zoom/scroll behavior of multiple inspection widgets, if possible/requested."""
        for insp in self._inspectors:
            insp.clearLinkedAxes()
            if self._should_link_viewers:
                insp.linkAxes(self._inspectors)

    def __addShortcuts(self):
        # Open file
        shortcut_open = QShortcut(QKeySequence('Ctrl+O'), self)
        shortcut_open.activated.connect(self.__onOpenShortcut)
        # Save file
        shortcut_save = QShortcut(QKeySequence('Ctrl+S'), self)
        shortcut_save.activated.connect(self.__onSaveShortcut)
        # Reload/change visualization
        shortcut_reload = QShortcut(QKeySequence('Ctrl+R'), self)
        shortcut_reload.activated.connect(self.__onReloadShortcut)
        # Close window
        shortcut_exit_q = QShortcut(QKeySequence('Ctrl+Q'), self)
        shortcut_exit_q.activated.connect(QApplication.instance().quit)
        shortcut_exit_w = QShortcut(QKeySequence('Ctrl+W'), self)
        shortcut_exit_w.activated.connect(QApplication.instance().quit)
        # Zooming
        shortcut_zoom_in = QShortcut(QKeySequence('Ctrl++'), self)
        shortcut_zoom_in.activated.connect(lambda: self.zoomImages(120))
        shortcut_zoom_in_fast = QShortcut(QKeySequence('Ctrl+Shift++'), self)
        shortcut_zoom_in_fast.activated.connect(lambda: self.zoomImages(1200))
        shortcut_zoom_out = QShortcut(QKeySequence('Ctrl+-'), self)
        shortcut_zoom_out.activated.connect(lambda: self.zoomImages(-120))
        shortcut_zoom_out_fast = QShortcut(QKeySequence('Ctrl+Shift+-'), self)
        shortcut_zoom_out_fast.activated.connect(lambda: self.zoomImages(-1200))
        # Scrolling
        shortcut_scroll_up = QShortcut(QKeySequence('Ctrl+Up'), self)
        shortcut_scroll_up.activated.connect(lambda: self.scrollImages(120, Qt.Vertical))
        shortcut_scroll_up_fast = QShortcut(QKeySequence('Ctrl+Shift+Up'), self)
        shortcut_scroll_up_fast.activated.connect(lambda: self.scrollImages(1200, Qt.Vertical))
        shortcut_scroll_down = QShortcut(QKeySequence('Ctrl+Down'), self)
        shortcut_scroll_down.activated.connect(lambda: self.scrollImages(-120, Qt.Vertical))
        shortcut_scroll_down_fast = QShortcut(QKeySequence('Ctrl+Shift+Down'), self)
        shortcut_scroll_down_fast.activated.connect(lambda: self.scrollImages(-1200, Qt.Vertical))
        shortcut_scroll_left = QShortcut(QKeySequence('Ctrl+Left'), self)
        shortcut_scroll_left.activated.connect(lambda: self.scrollImages(120, Qt.Horizontal))
        shortcut_scroll_left_fast = QShortcut(QKeySequence('Ctrl+Shift+Left'), self)
        shortcut_scroll_left_fast.activated.connect(lambda: self.scrollImages(1200, Qt.Horizontal))
        shortcut_scroll_right = QShortcut(QKeySequence('Ctrl+Right'), self)
        shortcut_scroll_right.activated.connect(lambda: self.scrollImages(-120, Qt.Horizontal))
        shortcut_scroll_right_fast = QShortcut(QKeySequence('Ctrl+Shift+Right'), self)
        shortcut_scroll_right_fast.activated.connect(lambda: self.scrollImages(-1200, Qt.Horizontal))
        # Scale to fit window
        shortcut_scale_fit = QShortcut(QKeySequence('Ctrl+F'), self)
        shortcut_scale_fit.activated.connect(self.scaleImagesFit)
        # Scale to original size
        shortcut_scale_original = QShortcut(QKeySequence('Ctrl+1'), self)
        shortcut_scale_original.activated.connect(self.scaleImagesOriginal)
        # Toggle tool tip display
        shortcut_toggle_tooltip = QShortcut(QKeySequence('Ctrl+T'), self)
        shortcut_toggle_tooltip.activated.connect(self.toggleTooltipDisplay)

    @Slot(int)
    def scrollImages(self, delta, orientation):
        for insp in self._inspectors:
            insp.scrollImage(delta, orientation)

    @Slot(int)
    def zoomImages(self, delta):
        for insp in self._inspectors:
            insp.zoomImage(delta)

    @Slot()
    def scaleImagesOriginal(self):
        for insp in self._inspectors:
            insp.setImageScaleAbsolute(1.0)

    @Slot()
    def scaleImagesFit(self):
        for insp in self._inspectors:
            insp.setImageScaleFit()

    @Slot()
    def toggleTooltipDisplay(self):
        self._display_tooltip = not self._display_tooltip
        if self._display_tooltip:
            self.showPixelValue(self.__getActiveInspector(), None)
        else:
            QToolTip.hideText()

    @Slot(int)
    def __fileHasBeenOpened(self, inspector_id):
        self.__updateWindowTitle()
        # Update handles for linked inspectors (since image viewers may have
        # been replaced by new objects)
        self.__linkInspectors()
        # Send a dummy resize event to ensure that the "image information label"
        # and input widgets of each InspectionWidget are properly resized.
        for insp in self._inspectors:
            insp.resizeEvent(QResizeEvent(insp.size(), QSize()))

    def __updateWindowTitle(self):
        if len(self._inspectors) < 2:
            data = self._inspectors[0].getData()
            data_type = self._inspectors[0].getDataType()
        else:
            data = [insp.getData() for insp in self._inspectors]
            data_type = [insp.getDataType() for insp in self._inspectors]
        self.setWindowTitle(
            Inspector.makeWindowTitle(
                self._user_defined_window_title, data, data_type))

    def __statusBarMessage(self, query):
        """
        Returns a message to be displayed upon the status bar showing
        the data point at the cursor position. Requires result of _queryDataLocation
        as input.
        """
        s = query['pos'] + ', ' + query['dtypestr'] + ': ' + query['rawstr']
        if query['currlayer'] is not None:
            s += ', Current layer: ' + query['currlayer']
        if query['pseudocol'] is not None:
            s += ', Pseudocolor: ' + query['pseudocol']
        return s

    def __tooltipMessage(self, query):
        """
        Returns a HTML formatted tooltip message showing the
        data point at the cursor position. Requires result of _queryDataLocation
        as input.
        """
        s = '<table><tr><td>Position:</td><td>' + query['pos'] + '</td></tr>'
        s += '<tr><td>' + query['dtypestr'] + ':</td><td>' + query['rawstr'] + '</td></tr>'
        if query['currlayer'] is not None:
            s += '<tr><td>Layer:</td><td>' + query['currlayer'] + '</td></tr>'
        if query['pseudocol'] is not None:
            s += '<tr><td>Colormap:</td><td> ' + query['pseudocol'] + '</td></tr>'
        if query['scale'] is not None:
            if query['scale'] < 0.01:
                sc = '< 1'
            else:
                sc = '{:d}'.format(int(query['scale']*100))
            s += '<tr><td>Scale:</td><td> ' + sc + '%</td></tr>'
        s += '</table>'
        return s

    @Slot(int, object)
    def showPixelValue(self, inspector_id, image_pos):
        """Invoked whenever the mouse position changed."""
        if image_pos is None:
            # Position will be None if the user scrolls/zooms via keyboard
            # shortcuts. Thus, update info for positoin under cursor:
            if not self._inspectors[inspector_id].underMouse():
                return
            image_pos = self._inspectors[inspector_id].pixelFromGlobal(QCursor.pos())
        q = self._inspectors[inspector_id].getPixelValue(image_pos.x(), image_pos.y())
        if q is None:
            QToolTip.hideText()
            self.statusBar().showMessage('')
            return
        self.statusBar().showMessage(self.__statusBarMessage(q))
        if self._display_tooltip:
            QToolTip.showText(QCursor().pos(), self.__tooltipMessage(q))

    def __getActiveInspector(self):
        """
        Returns the index of the currently "active" inspection widget. If
        there are multiple inspection widgets, the one currently under the
        mouse is considered active.
        If no widget is under the mouse, this falls back to the first
        inspection widget.
        """
        for inspector_id in range(len(self._inspectors)):
            if self._inspectors[inspector_id].underMouse():
                return inspector_id
        return 0

    @Slot()
    def __onOpenShortcut(self):
        inspector_id = self.__getActiveInspector()
        self._inspectors[inspector_id].showFileOpenDialog()

    @Slot()
    def __onSaveShortcut(self):
        inspector_id = self.__getActiveInspector()
        self._inspectors[inspector_id].showFileSaveDialog()
    
    @Slot()
    def __onReloadShortcut(self):
        inspector_id = self.__getActiveInspector()
        self._inspectors[inspector_id].showVisualizationChangeDialog()


def inspect(
        data: Union[np.ndarray, Tuple[np.ndarray, ...]],
        data_type: DataType = None,
        flip_channels: bool =False,
        label: str = None,
        display_settings: dict = None,
        initial_window_size: Tuple[int, int] = None,
        max_num_widgets_per_row: int = 3,
        force_linked_viewers: bool = False,
        categorical_labels: Union[dict, Tuple[dict, ...]] = None):
    """
    Opens a GUI to visualize the given image data.

    Args:
      data: numpy ndarray to be visualized. If you want to inspect
        several images at once, data may be a tuple of numpy darray.

      data_type: A DataType enumeration or None. If your input "data" is a
        tuple, data_type must be None or a tuple of DataType.
        Specifying this is necessary/useful if you want to inspect
        a label image: there's no (easy) way of automatically
        distinguish a monochrome image from a label image if your
        input "data" is uint8.
        If None, the "Inspector" will try to guess the data type from
        the input data.shape and data.dtype, see DataType.fromData().

      flip_channels: This qt window works with RGB images, so flip_channels must
        be set True if your data is BGR.

      label: Optionally specify a window title.

      display_settings: A dictionary of display settings in case you want to
        restore the previous settings. The current settings are
        returned by this function.

      initial_window_size: Optionally resize the window to the given (width,
        height) window size.

      max_num_widgets_per_row: If the input "data" is a tuple/list of
        multiple images, the GUI will show a grid of
        floor(N/num_per_row) x num_per_row inspection widgets.

      force_linked_viewers: If you inspect multiple images at once ("data"
        is a tuple), the image viewers will only be linked (i.e.
        scroll/zoom simultaneously) if they have the same width
        and height. If your input sizes differ, you can set this
        flag to force linked viewers.

      categorical_labels: if data_type is CATEGORICAL, you can provide custom
        labels to be displayed on the colorbar (as a dictionary,
        mapping data values to label strings). If the input data
        is a tuple/list, this should be provided as:
        * a tuple/list of such dictionaries (if different for each
          inputs or not all inputs are categorical), or
        * a single dictionary if all inputs show the same labels.

    Returns:
      The window's exit code and a dictionary of currently used display
        settings.
    """
    if flip_channels:
        data = imutils.flip_layers(data)
    # If window title is not provided, make one (indicating the data type).
    app_label = Inspector.makeWindowTitle(label, data, data_type)

    app = QApplication([app_label])

    if initial_window_size is None:
        from qtpy.QtGui import QGuiApplication
        initial_window_size = QGuiApplication.primaryScreen().availableGeometry().size() * 0.7
    else:
        initial_window_size = QSize(initial_window_size[0], initial_window_size[1])

    main_widget = Inspector(
        data=data,
        data_type=data_type,
        display_settings=display_settings,
        initial_window_size=initial_window_size,
        window_title=label,
        max_num_widgets_per_row=max_num_widgets_per_row,
        force_linked_viewers=force_linked_viewers,
        categorical_labels=categorical_labels)
    main_widget.show()
    rc = app.exec_()
    # Query the viewer settings (in case the user wants to restore them for the
    # next image)
    display_settings = main_widget.currentDisplaySettings()
    return rc, display_settings


if __name__ == '__main__':
    print('Please refer to the example application at ../examples/demo.py!')
    print('If not included in your package, see https://github.com/snototter/iminspect')
