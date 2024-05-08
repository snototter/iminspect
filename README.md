# iminspect
[![View on PyPI](https://img.shields.io/pypi/v/iminspect.svg)](https://pypi.org/project/iminspect)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/iminspect.svg)](https://pypi.org/project/iminspect)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/snototter/iminspect/blob/master/LICENSE?raw=true)

A python utility package for image/matrix visualization.

![Application logo](https://github.com/snototter/iminspect/blob/master/screenshots/logo.png?raw=true "Application logo")

Moving from MATLAB to python I was missing fast and easy-to-use inspection tools for image data.
Thus, `iminspect` provides a collection of visualization/inspection capabilities along with a simplistic Qt-based GUI.
The goal is to enable quick and easy visualization/analysis of:
* color images,
* monochrome images (i.e. any type of 2D matrices),
* label images (i.e. categorical data),
* binary masks,
* depth maps, and
* optical flow data.


## Qt Backend
`iminspect` requires a [Qt](https://www.qt.io/) backend. In Python, you need to
either install [PyQt](https://www.riverbankcomputing.com/software/pyqt/download)
or [PySide](https://doc.qt.io/qtforpython-6/).  
The default installation **will not install** any of these backends, you have
to select one on your own.

Optionally, you can install `iminspect` with a specific backend. Currently,
`pyqt5`, `pyqt6`, `pyside2`, and `pyside6` are supported:
```bash
# PyQt5
python3 -m pip install "iminspect[pyqt5]"

# OR PyQt6
python3 -m pip install "iminspect[pyqt6]"

# OR PySide2
python3 -m pip install "iminspect[pyside2]"

# OR PySide6
python3 -m pip install "iminspect[pyside6]"
```

## Example usage (within a Python script):
```python
from iminspect.inspector import inspect, DataType
import numpy as np

# Show random noise image:
inspect(np.random.rand(4096,4096) - 0.5)

# Show as class labels:
inspect((np.random.rand(16,16) * 1e2 % 5).astype(np.int16), data_type=DataType.CATEGORICAL)

# Show two images next to each other, e.g. useful to analyse RGB and
# corresponding depth, or RGB and corresponding optical flow:
inspect((data_color, data_depth))
# or specify the data types manually:
inspect((rgb, flow), data_type=(DataType.COLOR, DataType.FLOW)))
```

Example: visualizing categorical data (i.e. labels)<br/>
![Screenshot categorical data](https://github.com/snototter/iminspect/blob/master/screenshots/categorical.jpg?raw=true "iminspect GUI")

Example: visualizing a mask image<br/>
![Screenshot binary data](https://github.com/snototter/iminspect/blob/master/screenshots/mask.jpg?raw=true "iminspect GUI")

Example: visualizing RGB image and optical flow<br/>
![Screenshot optical flow](https://github.com/snototter/iminspect/blob/master/screenshots/rgb-flow.jpg?raw=true "iminspect GUI")


## Example usage (standalone):
The `iminspect` package can be run as a standalone application, so you could create a launcher, add it to your system's binary/executable path, etc.
You can either do this manually via the following steps or try the `standalone/install-...` scripts.

1. Set up a virtual environment (in this example, I'll use a separate `util-iminspect` folder to install the `iminspect` package):
    ```bash
    cd desired/installation/path
    python3 -m venv util-iminspect
    source util-iminspect/bin/activate
    pip install -U pip
    pip install iminspect
    ```
2. Run `iminspect` standalone via:
    ```bash
    desired/installation/path/util-iminspect/bin/python3 -m iminspect
    ```


## Custom input widgets:
The `iminspect.inputs` subpackage provides common user input widgets, e.g. to select a rectangular region-of-interest, enter an IP address, etc. See the `examples/inputs_demo.py` application on how to use it. Exemplary screenshot:<br/>
![Screenshot inputs demo](https://github.com/snototter/iminspect/blob/master/screenshots/input-widgets.jpg?raw=true "Common input widgets")


## UI Documentation
* To inspect a data point/pixel, just move the mouse above it.
* Zooming:
  * `Ctrl+Wheel` to zoom in/out.
  * `Ctrl+Shift+Wheel` to speed up zooming.
  * `Ctrl+{+|-}` to zoom in/out.
  * `Ctrl+Shift+{+|-}` to zoom in/out faster.
  * `Ctrl+F` to zoom such that the image fills the available canvas.
  * `Ctrl+1` to scale to original size.
* Scrolling:
  * `Wheel` scrolls up/down.
  * `Shift+Wheel` speeds up scrolling.
  * `Ctrl+{Up|Down|Left|Right}` to scroll using keyboard.
  * `Ctrl+Shift+{Up|Down|Left|Right}` to scroll faster/further. 
  * Press and move left/right button to drag the image if zoomed in.
* Keyboard shortcuts:
  * `Ctrl+Q` and `Ctrl+W` close the inspection GUI.
  * `Ctrl+O` shows a dialog to open another file.
  * `Ctrl+S` shows a dialog to save either the (raw) input or its current visualization.
  * `Ctrl+T` toggles tool tip display when moving the mouse over the data.
  * `Ctrl+R` reloads the current data such that the user can select a different visualization/data type.


## Changelog
* `1.4.1`
  * Adds the missing asset.
* `1.4.0`
  * Updates the build process, switching to [pyproject.toml](https://pip.pypa.io/en/stable/reference/build-system/pyproject-toml/)
  * Users can choose which Qt/PySide version should be used via the package extras.
* `1.3.11`
  * Prevents a `TypeError` that occurs for some mouse wheel zoom actions on recent OS/Qt versions.
  * Github workflow updates
  * Remove Python EOL versions
  * Fix OS & Python setup for CI test runner
  * Update PyPI action to use [Trusted Publishing](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/) / [OpenID Connect (OIDC)](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-pypi)
* `1.3.10`
  * Added utility scripts for [standalone installation](https://github.com/snototter/iminspect/blob/master/standalone/install-standalone-ubuntu-18.04.sh) (on Ubuntu).
  * Clarified standalone usage example.
  * Minor tweaks to the `inputs` subpackage.
* `1.3.9`
  * Handle non-finite values: Info/caution message shows in the data summary label, non-finite values are ignored in computing the data statistics.
  * Option (Shortcut and toolbar button) to reload the currently inspected data with a different visualization/data type.
  * Added application icon.
* `1.3.8`
  * Added support for opening files via dropping them from external image viewer applications. Tested with common Linux viewers (`eog` and `geeqie`).
* `1.3.7`
  * Support opening files by dropping them into the viewer.
  * Added `__main__` to run module (open the inspector) via `python -m iminspect`
* `1.3.6`
  * Inspector handles 1D inputs.
  * Minor tweaks to the `inputs` subpackage.
* `1.3.5`
  * Bug fix - rounding issues during initialization of custom slider widgets (which use floats).
* `1.3.4`
  * Minor tweaks to the `inputs` subpackage.
* `1.3.3`
  * Add functionality to open the inspector without data (in case you want to load from disk).
* `1.3.2`
  * Added color picker widget to `inputs`.
  * Support multiple file selection dialog.
* `1.3.1`
  * Minor extensions to user `inputs` subpackage.
* `1.3.0`
  * Added a range slider to adjust visualization limits on the fly.
  * Image viewer (canvas) now supports dragging.
  * Support toggling the tool tip display.
  * Support adding custom labels for categorical data.
  * Fix running `inputs.py` as standalone demo (relative import confusion).
* `1.2.0`
  * Support multi-channel input data (with more than 4 channels).
  * Support analysing multiple images at once, e.g. color images and corresponding optical flow.
  * Major refactoring under the hood.
* `1.1.0`
  * Support saving visualization and raw input data to disk.
  * Added shorthand wrapper to `inspect()` call.
  * UI improvements/layout changes.
  * Fixed typos such as `DataType.CATEGORICAL`.
  * Added support for partially transparent images (i.e. RGBA).
* `1.0.0`
  * Major code refactoring: use data type enum instead of various flags (this breaks previous inspect() calls).
  * Optical flow support.
  * Load another file from disk (via `Ctrl+O`).
  * Usability improvements, e.g. restore display settings when opening similar data type, handle file loading errors, etc.
* `0.2.0`
  * Major refactoring: moved image utils and colorizing code to separate [vito](https://github.com/snototter/vito) package.
  * Usability improvements: keyboard shortcuts for zooming, scaling and scrolling.
* `0.1.2`
  * Added tests for non-GUI functionality.
  * Integrate github runners for test/build/deploy.
  * Fix definition for colormap gray.
* `0.1.1`
  * Additional features:
    * ImageCanvas supports ROI selection (useful for custom input widgets).
  * Refactoring:
    * Clean up imports.
    * Make pylint/flake8 happier.
  * Fixes:
    * Adjust scrollbars when zooming multiple linked ImageCanvas.
* `0.1.0` - Initial public release.

