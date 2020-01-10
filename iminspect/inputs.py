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
    QSlider, QCheckBox, QFileDialog, QComboBox, QLineEdit, QSizePolicy
from PyQt5.QtCore import pyqtSignal, Qt, QSize, QRegExp
from PyQt5.QtGui import QRegExpValidator, QFontDatabase


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
        self.setLayout(layout)

    def get_input(self):
        return self._cb.isChecked()

    def set_value(self, b):
        self._cb.setChecked(b)


class SliderSelectionWidget(InputWidget):
    def __init__(
            self, label, min_value, max_value, num_steps, initial_value=None,
            label_format='{:d}', parent=None, min_label_width=None):
        super(SliderSelectionWidget, self).__init__(parent)
        self._min_value = min_value
        self._max_value = max_value
        self._num_steps = num_steps
        self._step_size = (max_value - min_value) / num_steps
        self._label_format = label_format

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
        if 'd' in self._label_format:
            return int(v)
        return v

    def __value_changed(self):
        val = self.__slider_value()
        self._slider_label.setText(self._label_format.format(val))
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
        self._combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if initial_selected_index is not None:
            self._combo.setCurrentIndex(initial_selected_index)

        self._combo.activated.connect(self._emit_value_change)

        layout.addWidget(self._combo)
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

    def __from_image(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select Image", "",
                    "Images (*.jpg *.jpeg *png);;All Files (*.*);;")
        if filename:
            # Load as numpy array
            import numpy as np
            from PIL import Image
            img_np = np.asarray(Image.open(filename).convert('RGB'))

            # Show modal dialog
            from imgview import RectSelectionDialog
            dlg = RectSelectionDialog(self)
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

        self._slider = SliderSelectionWidget('Slide int:', 50, 100, 10, label_format='{:3d}', min_label_width=150)
        main_layout.addWidget(self._slider)
        self._sliderf = SliderSelectionWidget('Slide float:', 0, 1, 10, label_format='{:3.1f}', min_label_width=150)
        main_layout.addWidget(self._sliderf)
        self._sliderf.setEnabled(False)
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
                self._dropdown, self._slider, self._sliderf, self._cb,
                self._roi]:
            print('Input "{}"'.format(w.get_input()))
        print('\n')


def run_demo():
    app = QApplication(['Input demo'])
    main_widget = InputDemoApplication()
    main_widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    run_demo()
