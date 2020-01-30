#!/usr/bin/env python
# coding=utf-8
"""
Standard widgets for user input.
They take care of adding a label to a default input widget, proper spacing,
etc. Additionally, they emit a single signal "value_changed" and provide a
"get_input()" function (because I'm too lazy to remember the correct getters
for all the Qt standard widgets).
"""

# TODO implement set_value for remaining widgets (currently only needed for
# checkboxes and dropdowns)

import os
import sys
from enum import Enum
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, \
    QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFrame, \
    QSlider, QCheckBox, QFileDialog, QComboBox, QLineEdit, QSizePolicy, \
    QColorDialog
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QSize, QRegExp, QEvent, QRect, QRectF
from PyQt5.QtGui import QRegExpValidator, QFontDatabase, QColor, QBrush, QPen, QPainter
from vito import imutils

from . import imgview


def format_int(v, digits=None):
    if digits is None:
        fs = '{:d}'
    else:
        fs = '{:' + str(digits) + 'd}'
    return fs.format(int(v))


def format_float(v, digits=None, after_comma=None):
    if digits is None:
        if after_comma is None:
            fs = '{:f}'
        else:
            fs = '{:.' + str(after_comma) + 'f}'
    else:
        if after_comma is None:
            fs = '{:' + str(digits) + 'f}'
        else:
            fs = '{:' + str(digits) + '.' + str(after_comma) + 'f}'
    return fs.format(float(v))


class HLine(QFrame):
    """A horizontal line (divider)."""
    def __init__(self, parent=None):
        super(HLine, self).__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class VLine(QFrame):
    """A vertical line (divider)."""
    def __init__(self, parent=None):
        super(VLine, self).__init__(parent)
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)


class InputWidget(QWidget):
    """Base class which defines the value-changed signal to be emitted."""
    value_changed = pyqtSignal(object)

    def __init__(self, parent=None):
        super(InputWidget, self).__init__(parent)

    def _emit_value_change(self):
        self.value_changed.emit(self.get_input())

    def value(self):
        return self.get_input()


class CheckBoxWidget(InputWidget):
    def __init__(self, label, is_checked=False, checkbox_left=False, parent=None, min_label_width=None):
        super(CheckBoxWidget, self).__init__(parent)
        lbl = QLabel(label)
        if min_label_width is not None:
            lbl.setMinimumWidth(min_label_width)

        self._cb = QCheckBox()
        self._cb.setChecked(is_checked)
        self._cb.setLayoutDirection(Qt.LeftToRight if checkbox_left else Qt.RightToLeft)
        self._cb.setStyleSheet("QCheckBox::indicator {width:18px; height:18px;};")
        self._cb.toggled.connect(self._emit_value_change)

        layout = QHBoxLayout()
        if checkbox_left:
            layout.addWidget(self._cb)
            layout.addWidget(lbl)
        else:
            layout.addWidget(lbl)
            layout.addWidget(self._cb)
        layout.addStretch()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def get_input(self):
        return self._cb.isChecked()

    def set_value(self, b):
        self._cb.setChecked(b)


class ColorIndicator(QWidget):
    """
    Draws a right aligned rectangle of dimension
    H x (width_factor * H) with the currently set color.
    H = widget.height() - 2*padding.
    If width_factor is negative, W = widget.width() - 2*padding.
    """
    clicked = pyqtSignal()

    def __init__(self, padding=0, width_factor=4, parent=None):
        super(ColorIndicator, self).__init__(parent)
        self._color = None
        self._padding = padding
        self._width_factor = width_factor
        self.setMinimumWidth(30)

    def set_color(self, color):
        self._color = color

    def set_padding(self, padding):
        self._padding = padding

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

    def paintEvent(self, event):
        if self._color is None:
            return
        painter = QPainter(self)
        painter.setPen(QPen(Qt.black, 1.5))
        painter.setRenderHint(QPainter.Qt4CompatiblePainting)
        brush = QBrush(self._color if self.isEnabled() else QColor(
            self._color.red(), self._color.green(), self._color.blue(), 100))
        painter.setBrush(brush)
        h = self.height() - 2*self._padding
        if self._width_factor <= 0:
            w = self.width() - 2*self._padding
        else:
            w = self._width_factor*h
        rect = QRectF(
            self.width() - w - self._padding,
            self._padding, w, h)
        painter.drawRoundedRect(rect,
            max(self._padding, 2), max(self._padding, 2))
        self.setMinimumWidth(w)


class ColorPickerWidget(InputWidget):
    def __init__(
            self, label, initial_color=(255, 255, 255), parent=None,
            min_label_width=None, padding=0, width_factor=3,
            with_alpha=False):
        super(ColorPickerWidget, self).__init__(parent)
        self._with_alpha = with_alpha
        self._color = initial_color
        if with_alpha and len(self._color) == 3:
            self._color = (*self._color, 255)

        lbl = QLabel(label)
        if min_label_width is not None:
            lbl.setMinimumWidth(min_label_width)

        self._color_indicator = ColorIndicator(width_factor=width_factor, padding=padding)

        self._color_indicator.set_color(self.qcolor())
        self._color_indicator.clicked.connect(self.__choose)

        layout = QHBoxLayout()
        layout.addWidget(lbl)
        layout.addWidget(self._color_indicator)
        layout.addStretch()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    @pyqtSlot()
    def __choose(self):
        opt = QColorDialog.DontUseNativeDialog
        if self._with_alpha:
            opt = opt | QColorDialog.ShowAlphaChannel
        c = QColorDialog.getColor(
            initial=self.qcolor(),
            parent=self,
            options=opt)
        if c.isValid():
            self.set_value((c.red(), c.green(), c.blue()))

    def qcolor(self):
        return QColor(*self._color)

    def get_input(self):
        return self._color

    def set_value(self, rgb):
        self._color = rgb
        self._color_indicator.set_color(self.qcolor())
        self.value_changed.emit(self.get_input())
        self.update()


class RangeSlider(QWidget):
    # Based on c++ version https://github.com/ThisIsClark/Qt-RangeSlider
    # TODO Implement keyboard support:
    # * Mouse selects handle for subsequent keyboard input
    # * Tab switches to upper handle, shift+tab to lower
    # * arrow keys increment by one
    # TODO Implement ticks

    # Padding between widget border and actual slider/bar
    HORIZONTAL_MARGIN = 1

    # Height of the slider's bar (i.e. the "line" behind the handles)
    SLIDER_BAR_HEIGHT = 4

    # The slider's handles will be drawn as squares with this side length
    HANDLE_SIDE_LENGTH = 13

    # Min/max has changed:
    rangeChanged = pyqtSignal(int, int)
    # Lower/left value has changed
    lowerValueChanged = pyqtSignal(int)
    # Upper/right value has changed
    upperValueChanged = pyqtSignal(int)

    def __init__(self, min_value=0, max_value=100,
            parent=None):
        super(RangeSlider, self).__init__()
        self._minimum = min_value
        self._maximum = max_value
        self._interval = max_value - min_value
        self._lower_value = min_value
        self._upper_value = max_value
        self._lower_handle_pressed = False
        self._upper_handle_pressed = False
        self._bg_color_enabled = QColor(0x1e, 0x90, 0xff)
        self._bg_color_disabled = Qt.darkGray
        self._bg_color = self._bg_color_enabled
        self._delta = 0
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMouseTracking(True)

    def range(self):
        return (self._minimum, self._maximum)

    def lowerValue(self):
        return self._lower_value

    def upperValue(self):
        return self._upper_value

    def value(self):
        return (self._lower_value, self._upper_value)

    def minimum(self):
        return self._minimum

    def maximum(self):
        return self._maximum

    def setMinimum(self, m):
        prev_range = self.range()
        if m <= self._maximum:
            self._minimum = m
        else:
            self._minimum = self._maximum
            self._maximum = m

        if prev_range[0] != self._minimum or prev_range[1] != self._maximum:
            self.__updateInterval()
            self.rangeChanged.emit(self._minimum, self._maximum)

    def setMaximum(self, m):
        prev_range = self.range()
        if m >= self._minimum:
            self._maximum = m
        else:
            self._maximum = self._minimum
            self._minimum = m
        if prev_range[0] != self._minimum or prev_range[1] != self._maximum:
            self.__updateInterval()
            self.rangeChanged.emit(self._minimum, self._maximum)

    def setRange(self, v_min, v_max):
        prev_range = self.range()
        if v_min < v_max:
            self._minimum = v_min
            self._maximum = v_max
        else:
            self._minimum = v_max
            self._maximum = v_min
        if prev_range[0] != self._minimum or prev_range[1] != self._maximum:
            self.__updateInterval()
            self.rangeChanged.emit(self._minimum, self._maximum)

    def __updateInterval(self):
        self._interval = self._maximum - self._minimum
        if self._lower_value < self._minimum:
            self.setLowerValue(self._minimum)
        if self._upper_value < self._minimum:
            self.setUpperValue(self._minimum)
        if self._lower_value > self._maximum:
            self.setLowerValue(self._maximum)
        if self._upper_value > self._maximum:
            self.setUpperValue(self._maximum)
        self.update()

    def setLowerValue(self, v):
        v = int(v)
        if v > self._maximum:
            v = self._maximum
        if v < self._minimum:
            v = self._minimum
        prev = self._lower_value
        self._lower_value = v
        if self._lower_value != prev:
            self.lowerValueChanged.emit(self._lower_value)
            self.update()

    def setUpperValue(self, v):
        v = int(v)
        if v > self._maximum:
            v = self._maximum
        if v < self._minimum:
            v = self._minimum
        prev = self._upper_value
        self._upper_value = v
        if self._upper_value != prev:
            self.upperValueChanged.emit(self._upper_value)
            self.update()

    def validWidth(self):
        return self.width() - RangeSlider.HORIZONTAL_MARGIN * 2 - RangeSlider.HANDLE_SIDE_LENGTH * 2

    def paintEvent(self, event):
        painter = QPainter(self)
        # Draw background
        bg_rect = QRectF(RangeSlider.HORIZONTAL_MARGIN,
            (self.height() - RangeSlider.SLIDER_BAR_HEIGHT) / 2,
            self.width() - RangeSlider.HORIZONTAL_MARGIN * 2,
            RangeSlider.SLIDER_BAR_HEIGHT)
        painter.setPen(QPen(Qt.gray, 0.8))
        painter.setRenderHint(QPainter.Qt4CompatiblePainting)
        bg_brush = QColor(0xD0, 0xD0, 0xD0)
        painter.setBrush(bg_brush)
        painter.drawRoundedRect(bg_rect, 1, 1)

        # Lower value handle rect
        painter.setPen(QPen(Qt.darkGray, 0.5))
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(0xFA, 0xFA, 0xFA)))
        lower_handle_rect = self.lowerHandleRect()
        painter.drawRoundedRect(lower_handle_rect, 2, 2)
        # Upper value handle rect
        upper_handle_rect = self.upperHandleRect()
        painter.drawRoundedRect(upper_handle_rect, 2, 2)

        # Handles
        painter.setRenderHint(QPainter.Antialiasing, False)
        bg_rect.setLeft(lower_handle_rect.right() + 0.5)
        bg_rect.setRight(upper_handle_rect.left() - 0.5)
        painter.setBrush(QBrush(self._bg_color))
        painter.drawRect(bg_rect)

    def lowerHandleRect(self):
        percentage = (self._lower_value - self._minimum) * 1.0 / self._interval
        return self.handleRect(percentage * self.validWidth() + RangeSlider.HORIZONTAL_MARGIN)

    def upperHandleRect(self):
        percentage = (self._upper_value - self._minimum) * 1.0 / self._interval
        return self.handleRect(percentage * self.validWidth()
            + RangeSlider.HORIZONTAL_MARGIN + RangeSlider.HANDLE_SIDE_LENGTH)

    def handleRect(self, left):
        return QRect(int(left), (self.height() - RangeSlider.HANDLE_SIDE_LENGTH) // 2,
            RangeSlider.HANDLE_SIDE_LENGTH, RangeSlider.HANDLE_SIDE_LENGTH)

    def mousePressEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._lower_handle_pressed = self.lowerHandleRect().contains(event.pos())
            self._upper_handle_pressed = not self._lower_handle_pressed and self.upperHandleRect().contains(event.pos())
            if self._lower_handle_pressed:
                self._delta = event.pos().x() - (self.lowerHandleRect().x() + RangeSlider.HANDLE_SIDE_LENGTH // 2)
            elif self._upper_handle_pressed:
                self._delta = event.pos().x() - (self.upperHandleRect().x() + RangeSlider.HANDLE_SIDE_LENGTH // 2)

            if event.pos().y() > 1 and event.pos().y() < self.height() - 1:
                step = 1 if (self._interval // 10) < 1 else self._interval // 10
                if event.pos().x() < self.lowerHandleRect().x():
                    self.setLowerValue(self._lower_value - step)
                elif event.pos().x() > self.lowerHandleRect().x() + RangeSlider.HANDLE_SIDE_LENGTH \
                        and event.pos().x() < self.upperHandleRect().x():
                    if event.pos().x() - (self.lowerHandleRect().x() + RangeSlider.HANDLE_SIDE_LENGTH) < \
                            (self.upperHandleRect().x() - (self.lowerHandleRect().x() + RangeSlider.HANDLE_SIDE_LENGTH)) / 2:
                        if self._lower_value + step < self._upper_value:
                            self.setLowerValue(self._lower_value + step)
                        else:
                            self.setLowerValue(self._upper_value)
                    else:
                        if self._upper_value - step > self._lower_value:
                            self.setUpperValue(self._upper_value - step)
                        else:
                            self.setUpperValue(self._lower_value)
                elif event.pos().x() > self.upperHandleRect().x() + RangeSlider.HANDLE_SIDE_LENGTH:
                    self.setUpperValue(self._upper_value + step)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            if self._lower_handle_pressed:
                if event.pos().x() - self._delta + RangeSlider.HANDLE_SIDE_LENGTH / 2 <= self.upperHandleRect().x():
                    self.setLowerValue((event.pos().x() - self._delta - RangeSlider.HORIZONTAL_MARGIN
                    - RangeSlider.HANDLE_SIDE_LENGTH / 2) * 1.0 / self.validWidth() * self._interval + self._minimum)
                else:
                    self.setLowerValue(self._upper_value)
            elif self._upper_handle_pressed:
                if self.lowerHandleRect().x() + RangeSlider.HANDLE_SIDE_LENGTH * 1.5 <= event.pos().x() - self._delta:
                    self.setUpperValue(
                        (event.pos().x() - self._delta - RangeSlider.HORIZONTAL_MARGIN
                        - RangeSlider.HANDLE_SIDE_LENGTH / 2 - RangeSlider.HANDLE_SIDE_LENGTH)
                        * 1.0 / self.validWidth() * self._interval + self._minimum)
                else:
                    self.setUpperValue(self._lower_value)

    def mouseReleaseEvent(self, event):
        self._lower_handle_pressed = False
        self._upper_handle_pressed = False

    def changeEvent(self, event):
        if event.type() == QEvent.EnabledChange:
            self._bg_color = self._bg_color_enabled if self.isEnabled() else self._bg_color_disabled
            self.update()

    def minimumSizeHint(self):
        return QSize(RangeSlider.HANDLE_SIDE_LENGTH * 2 + RangeSlider.HORIZONTAL_MARGIN * 2,
            RangeSlider.HANDLE_SIDE_LENGTH)


class RangeSliderSelectionWidget(InputWidget):
    def __init__(
            self, label, min_value=0, max_value=100,
            initial_lower_value=None, initial_upper_value=None,
            value_format_fx=format_int,
            min_label_width=None, parent=None):
        super(RangeSliderSelectionWidget, self).__init__(parent)
        layout = QHBoxLayout()
        lbl = QLabel(label, parent=self)
        if min_label_width is not None:
            lbl.setMinimumWidth(min_label_width)
        layout.addWidget(lbl)

        self._lbl_lower = QLabel(' ', parent=self)
        self._lbl_lower.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self._lbl_lower)

        self._slider = RangeSlider(min_value=min_value, max_value=max_value, parent=self)
        if initial_lower_value is not None:
            self._slider.setLowerValue(initial_lower_value)
        if initial_upper_value is not None:
            self._slider.setUpperValue(initial_upper_value)
        self._slider.lowerValueChanged.connect(self.__slider_changed)
        self._slider.upperValueChanged.connect(self.__slider_changed)
        self._slider.rangeChanged.connect(lambda a, b: self.__slider_changed)
        layout.addWidget(self._slider)

        self._lbl_upper = QLabel(' ', parent=self)
        layout.addWidget(self._lbl_upper)
        self.set_value_format_fx(value_format_fx)

        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.__slider_changed()

    def set_value_format_fx(self, fx):
        self.__value_format_fx = fx
        if self.__value_format_fx is not None:
            # Set label text to the extremal values, so we can fix the width,
            # e.g. "False" vs "True"
            self._lbl_upper.setText(self.__value_format_fx(self._slider.minimum()))
            max_width = self._lbl_upper.sizeHint().width()
            self._lbl_upper.setText(self.__value_format_fx(self._slider.maximum()))
            max_width = max(max_width, self._lbl_upper.sizeHint().width())
            self._lbl_upper.setFixedWidth(max_width)
            self._lbl_lower.setFixedWidth(max_width)
            # Adjust the text:
            self._lbl_lower.setText(self.__value_format_fx(self._slider.lowerValue()))
            self._lbl_upper.setText(self.__value_format_fx(self._slider.upperValue()))

    def __slider_changed(self, _=None):
        v = self._slider.value()
        if self.__value_format_fx is not None:
            self._lbl_lower.setText(self.__value_format_fx(v[0]))
            self._lbl_upper.setText(self.__value_format_fx(v[1]))
        self._emit_value_change()

    def get_input(self):
        return self._slider.value()

    def set_value(self, v):
        # v must be tuple or list, array-like
        self._slider.setLowerValue(v[0])
        self._slider.setUpperValue(v[1])

    def set_range(self, v_min, v_max):
        self._slider.setRange(v_min, v_max)

    def get_range(self):
        return self._slider.range()


class SliderSelectionWidget(InputWidget):
    def __init__(
            self, label, min_value=0, max_value=100, num_steps=10,
            initial_value=None,
            value_format_fx=lambda v: format_int(v, 3),  # Maps slider value => string
            min_label_width=None,
            parent=None):
        super(SliderSelectionWidget, self).__init__(parent)
        self._min_value = min_value
        self._max_value = max_value
        self._num_steps = num_steps
        self._step_size = (max_value - min_value) / num_steps
        self.__value_format_fx = value_format_fx

        layout = QHBoxLayout()
        lbl = QLabel(label)
        if min_label_width is not None:
            lbl.setMinimumWidth(min_label_width)
        layout.addWidget(lbl)

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setMinimum(0)
        self._slider.setMaximum(num_steps)
        self._slider.setTickPosition(QSlider.TicksBelow)
        self._slider.valueChanged.connect(self.__value_changed)
        layout.addWidget(self._slider)

        self._slider_label = QLabel(' ')
        layout.addWidget(self._slider_label)

        # Set label to maximum value, so we can fix the width
        self._slider_label.setText(value_format_fx(max_value))
        self._slider_label.setFixedWidth(self._slider_label.sizeHint().width())

        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        if initial_value is None:
            self._slider.setValue(self.__to_slider_value(min_value))
        else:
            self._slider.setValue(self.__to_slider_value(initial_value))
        self.__value_changed()

    def __to_slider_value(self, value):
        v = (value - self._min_value)/self._step_size
        return v

    def __slider_value(self):
        v = self._slider.value()
        v = self._min_value + v * self._step_size
        # if 'd' in self._label_format:
        #     return int(v)
        return v

    def __value_changed(self):
        val = self.__slider_value()
        self._slider_label.setText(self.__value_format_fx(val))
        self._emit_value_change()

    def get_input(self):
        return self.__slider_value()

    def set_value(self, v):
        self._slider.setValue(self.__to_slider_value(v))
        self.__value_changed()


class DropDownSelectionWidget(InputWidget):
    def __init__(self, label, values, parent=None, min_label_width=None,
            initial_selected_index=None):
        """values = [(id, txt), (id, txt), ...]"""
        super(DropDownSelectionWidget, self).__init__(parent)
        layout = QHBoxLayout()
        lbl = QLabel(label)
        if min_label_width is not None:
            lbl.setMinimumWidth(min_label_width)
        layout.addWidget(lbl)
        layout.addStretch()

        self._combo = QComboBox(self)
        for v in values:
            self._combo.addItem(v[1], v[0])
        self._combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        if initial_selected_index is not None:
            self._combo.setCurrentIndex(initial_selected_index)

        self._combo.activated.connect(self._emit_value_change)
        layout.addWidget(self._combo)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def select_index(self, idx):
        self._combo.setCurrentIndex(idx)

    def get_input(self):
        return (self._combo.currentData(), self._combo.currentText())

    def set_value(self, id):
        """Selects the drop down element by its id (the one you specify
        upon creation of this widget)."""
        if id is tuple:
            eid = id[0]
        else:
            eid = id
        idx = self._combo.findData(eid)
        if idx != -1:
            self.select_index(idx)


class SizeWidget(InputWidget):
    def __init__(self, label, width=None, height=None, show_aspect_ratio_buttons=True, parent=None, min_label_width=None):
        super(SizeWidget, self).__init__(parent)
        layout = QHBoxLayout()
        lbl = QLabel(label)
        if min_label_width is not None:
            lbl.setMinimumWidth(min_label_width)
        layout.addWidget(lbl)
        layout.addStretch()

        self._w_edit = QLineEdit()
        self._w_edit.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        self._w_edit.setValidator(QRegExpValidator(QRegExp("[0-9]*"), self._w_edit))
        self._w_edit.setAlignment(Qt.AlignRight)
        self._w_edit.setMinimumWidth(50)
        self._w_edit.editingFinished.connect(self._emit_value_change)
        if width is not None:
            self._w_edit.setText('{:d}'.format(width))
        layout.addWidget(self._w_edit)

        layout.addWidget(QLabel('x'))

        self._h_edit = QLineEdit()
        self._h_edit.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        self._h_edit.setValidator(QRegExpValidator(QRegExp("[0-9]*"), self._h_edit))
        self._h_edit.setAlignment(Qt.AlignLeft)
        self._h_edit.setMinimumWidth(50)
        self._h_edit.editingFinished.connect(self._emit_value_change)
        if height is not None:
            self._h_edit.setText('{:d}'.format(height))
        layout.addWidget(self._h_edit)

        if show_aspect_ratio_buttons:
            # Include buttons for auto-completion
            btn4to3 = QPushButton('4:3')
            btn4to3.clicked.connect(self.__complete_4to3)
            btn4to3.setMinimumWidth(40)
            layout.addWidget(btn4to3)
            btn16to9 = QPushButton('16:9')
            btn16to9.clicked.connect(self.__complete_16to9)
            btn16to9.setMinimumWidth(40)
            layout.addWidget(btn16to9)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def __wh(self):
        tw = self._w_edit.text()
        if tw:
            w = int(tw)
        else:
            w = None
        th = self._h_edit.text()
        if th:
            h = int(th)
        else:
            h = None
        return w, h

    def get_input(self):
        w, h = self.__wh()
        if w is None or h is None:
            return (None, None)
        return (w, h)

    def __complete(self, w_ratio, h_ratio):
        w, h = self.__wh()
        if w is None and h is None:
            return
        if w is not None:
            h = int(w/w_ratio * h_ratio)
            self._h_edit.setText('{:d}'.format(h))
        else:
            w = int(h/h_ratio * w_ratio)
            self._w_edit.setText('{:d}'.format(w))
        self._emit_value_change()

    def __complete_4to3(self):
        self.__complete(4, 3)

    def __complete_16to9(self):
        self.__complete(16, 9)


class Ip4InputWidget(InputWidget):
    def __init__(self, label, ip_address=None, parent=None, min_label_width=None):
        super(Ip4InputWidget, self).__init__(parent)
        layout = QHBoxLayout()
        lbl = QLabel(label)
        if min_label_width is not None:
            lbl.setMinimumWidth(min_label_width)
        layout.addWidget(lbl)
        layout.addStretch()

        self._ip_edit = QLineEdit()
        self._ip_edit.setInputMask('000.000.000.000;_')
        self._ip_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._ip_edit.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        self._ip_edit.setAlignment(Qt.AlignRight)
        self._ip_edit.editingFinished.connect(self._emit_value_change)
        if ip_address is not None:
            self._ip_edit.setText(ip_address)
        layout.addWidget(self._ip_edit)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def get_input(self):
        ip = self._ip_edit.text()
        tokens = ip.split('.')
        if len(tokens) != 4 or any([len(t) == 0 for t in tokens]):
            return None
        return ip


class SelectDirEntryType(Enum):
    """Enumeration of supported file/folder selection widgets."""
    EXISTING_FOLDER = 1
    FILENAME_OPEN = 2
    FILENAME_SAVE = 3


class SelectDirEntryWidget(InputWidget):
    EMPTY_SELECTION = '---'

    def __init__(
            self, label, selection_type, parent=None, filters="All Files (*.*)",
            initial_filter='', min_label_width=None, relative_base_path=None):
        """
        :param label: Text to display
        :param selection_type: See SelectDirEntryType
        :param filters: File filters for QFileDialog
        :param initial_filter: Initial file filter for QFileDialog
        :param min_label_width: Min. width of the label (for nicer alignment)
        :param relative_base_path: If set, get_input() returns a path relative
                to this relative_base_path
        """
        super(SelectDirEntryWidget, self).__init__(parent)
        self._selection = None
        self._filters = filters
        self._initial_filter = initial_filter
        self._relative_base_path = relative_base_path

        layout = QHBoxLayout()
        lbl = QLabel(label)
        if min_label_width is not None:
            lbl.setMinimumWidth(min_label_width)
        layout.addWidget(lbl)
        layout.addStretch()

        self._selection_label = QLabel(type(self).EMPTY_SELECTION)
        layout.addWidget(self._selection_label)

        self._btn = QPushButton('Select')
        layout.addWidget(self._btn)
        if selection_type == SelectDirEntryType.EXISTING_FOLDER:
            self._btn.clicked.connect(self.__select_folder)
        elif selection_type == SelectDirEntryType.FILENAME_OPEN:
            self._btn.clicked.connect(self.__select_open_file)
        elif selection_type == SelectDirEntryType.FILENAME_SAVE:
            self._btn.clicked.connect(self.__select_save_file)
        else:
            raise NotImplementedError('Type not supported')
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def open_dialog(self):
        self._btn.click()

    def get_input(self):
        return self._selection

    def __set_selection(self, selection):
        if selection:
            if self._relative_base_path is not None:
                selection = os.path.relpath(selection, self._relative_base_path)
            self._selection = selection
            self._selection_label.setText(selection)  # TODO cut off string if longer than X chars
        else:
            self._selection = None
            self._selection_label.setText(type(self).EMPTY_SELECTION)
        self._emit_value_change()

    def __select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select a folder",
                '' if self._selection is None else self._selection,
                QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog)
        self.__set_selection(folder)

    def __select_open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select file", "", self._filters,
            self._initial_filter, QFileDialog.DontUseNativeDialog)
        self.__set_selection(filename)

    def __select_save_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Select file", "", self._filters,
            self._initial_filter, QFileDialog.DontUseNativeDialog)
        self.__set_selection(filename)


class RoiSelectWidget(InputWidget):
    def __init__(self, label, roi=None, parent=None, min_label_width=None):
        super(RoiSelectWidget, self).__init__(parent)
        layout = QHBoxLayout()
        lbl = QLabel(label)
        if min_label_width is not None:
            lbl.setMinimumWidth(min_label_width)
        layout.addWidget(lbl)
        layout.addStretch()

        self._line_edits = list()
        lbls = ['L:', 'T:', 'W:', 'H:']
        for idx in range(4):
            layout.addWidget(QLabel(lbls[idx]))

            le = QLineEdit()
            le.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
            le.setValidator(QRegExpValidator(QRegExp("[0-9]*"), le))
            le.setAlignment(Qt.AlignRight)
            le.setMinimumWidth(50)
            le.editingFinished.connect(self._emit_value_change)
            if roi is not None and roi[idx] is not None:
                le.setText('{}'.format(roi[idx]))
            layout.addWidget(le)
            self._line_edits.append(le)

        btn = QPushButton('From Image')
        btn.clicked.connect(self.__from_image)
        layout.addWidget(btn)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def get_input(self):
        rect = list()
        for i in range(4):
            txt = self._line_edits[i].text()
            if txt:
                rect.append(int(txt))
            else:
                rect.append(None)
        if any([v is None for v in rect]):
            return (None, None, None, None)
        return rect

    def __rect_selected(self, rect):
        if rect is None:
            rect = (None, None, None, None)
        for i in range(len(rect)):
            txt = '' if rect[i] is None else '{:d}'.format(rect[i])
            self._line_edits[i].setText(txt)
        self._emit_value_change()

    def __from_image(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select Image", "",
                    "Images (*.jpg *.jpeg *png);;All Files (*.*);;")
        if filename:
            # Show modal dialog
            img_np = imutils.imread(filename)
            dlg = imgview.RectSelectionDialog(self)
            dlg.rectSelected.connect(self.__rect_selected)
            dlg.showImage(img_np)
            dlg.setRectangle(self.get_input())
            dlg.exec()


class InputDemoApplication(QMainWindow):
    """Demo, showing what you can do with custom inputs"""
    def __init__(self):
        super(InputDemoApplication, self).__init__()
        self.__prepare_layout()

    def __prepare_layout(self):
        self._main_widget = QWidget()
        main_layout = QVBoxLayout()

        self._folder_widget = SelectDirEntryWidget('Select folder:',
                SelectDirEntryType.EXISTING_FOLDER, min_label_width=150,
                relative_base_path=os.getcwd())
        main_layout.addWidget(self._folder_widget)
        main_layout.addWidget(HLine())

        self._file_widget_open = SelectDirEntryWidget('Select file to open:',
                SelectDirEntryType.FILENAME_OPEN, min_label_width=150,
                relative_base_path=os.getcwd())
        main_layout.addWidget(self._file_widget_open)
        main_layout.addWidget(HLine())

        self._file_widget_save = SelectDirEntryWidget('Select file to save:',
                SelectDirEntryType.FILENAME_SAVE,
                filters="PDFs (*.pdf);;Images (*.jpg *.jpeg *.png);;", min_label_width=150)
        main_layout.addWidget(self._file_widget_save)
        main_layout.addWidget(HLine())

        self._ip_widget = Ip4InputWidget('IP Address:', '127.0.0.1', min_label_width=150)
        main_layout.addWidget(self._ip_widget)
        main_layout.addWidget(HLine())

        self._size_widget = SizeWidget('Image size:', 640, 480, min_label_width=150)
        main_layout.addWidget(self._size_widget)
        main_layout.addWidget(HLine())

        self._dropdown = DropDownSelectionWidget('Choose wisely:',
                [(1, 'foo'), (2, 'bar'), (3, 'blub')], min_label_width=150)
        main_layout.addWidget(self._dropdown)
        main_layout.addWidget(HLine())

        self._slider = SliderSelectionWidget('Slide int:', 50, 100, 10,
            value_format_fx=lambda v: format_int(v, 4), min_label_width=150)

        main_layout.addWidget(self._slider)
        self._sliderf = SliderSelectionWidget('Slide float:', 0, 1, 10,
            value_format_fx=lambda v: format_float(v, 3, 1), min_label_width=150)
        main_layout.addWidget(self._sliderf)
        self._sliderf.setEnabled(False)
        main_layout.addWidget(HLine())

        self._slider_range = RangeSliderSelectionWidget('Range slider:', 0, 100,
            value_format_fx=lambda v: format_int(v, 4), min_label_width=150)
        main_layout.addWidget(self._slider_range)
        main_layout.addWidget(HLine())

        self._cb = CheckBoxWidget('Check me', is_checked=True, min_label_width=150)
        main_layout.addWidget(self._cb)
        main_layout.addWidget(HLine())

        self._roi = RoiSelectWidget('ROI', roi=(10, 20, 50, 30), min_label_width=150)
        main_layout.addWidget(self._roi)
        main_layout.addWidget(HLine())

        main_layout.addStretch()
        self._btn_query = QPushButton('Query all widgets')
        self._btn_query.clicked.connect(self._query)
        main_layout.addWidget(self._btn_query)

        self._folder_widget.value_changed.connect(self._val_changed)
        self._file_widget_open.value_changed.connect(self._val_changed)
        self._file_widget_save.value_changed.connect(self._val_changed)
        self._ip_widget.value_changed.connect(self._val_changed)
        self._size_widget.value_changed.connect(self._val_changed)
        self._dropdown.value_changed.connect(self._val_changed)
        self._slider.value_changed.connect(self._val_changed)
        self._sliderf.value_changed.connect(self._val_changed)
        self._slider_range.value_changed.connect(self._val_changed)
        self._cb.value_changed.connect(self._val_changed)
        self._roi.value_changed.connect(self._val_changed)

        self._main_widget.setLayout(main_layout)
        self.setCentralWidget(self._main_widget)
        self.resize(QSize(640, 480))

    def _val_changed(self, value):
        sender = self.sender()
        print('Some value changed: ', sender.get_input())

    def _query(self):
        print('Query all widgets:')
        for w in [self._folder_widget, self._file_widget_open,
                self._file_widget_save, self._ip_widget, self._size_widget,
                self._dropdown, self._slider, self._sliderf, self._slider_range,
                self._cb, self._roi]:
            print('Input "{}"'.format(w.get_input()))
        print('\n')


def run_demo():
    print('########################################################\n')
    print('Demonstration of custom (labelled) input widgets.\n')
    print('########################################################')

    app = QApplication(['Input demo'])
    main_widget = InputDemoApplication()
    main_widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    run_demo()
