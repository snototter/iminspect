# iminspect
[![View on PyPI](https://img.shields.io/pypi/v/iminspect.svg)](https://pypi.org/project/iminspect)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/snototter/iminspect/blob/master/LICENSE?raw=true)

A python utility package for image/matrix visualization.

Moving from MATLAB to python I was missing basic inspection tools for image data.
Thus, `iminspect` provides a collection of basic visualization/inspection capabilities along with a minimalist Qt-based GUI.
The goal is to allow quick and easy visualization/analysis of:
* color images,
* monochrome images (i.e. any type of 2D matrices),
* label images (i.e. categorical data),
* binary masks,
* depth maps, and
* optical flow data.


## Dependencies
* `numpy`, for matrix manipulation
* `PyQt5`, for the graphical user interface
* `qimage2ndarray`, to convert numpy ndarrays to Qt images
* `vito`, a lightweight vision tool package


## Example usage:
```python
from iminspect.inspector import inspect, DataType
import numpy as np

# Show random noise image:
inspect(np.random.rand(4096,4096) - 0.5)

# Show as class labels:
inspect((np.random.rand(16,16) * 1e2 % 5).astype(np.int16), data_type=DataType.CATEGORICAL)
```

Example: visualizing categorical data (i.e. labels)<br/>
![Screenshot categorical data](https://github.com/snototter/iminspect/blob/master/screenshots/categorical.jpg?raw=true "iminspect GUI")

Example: visualizing a mask image<br/>
![Screenshot binary data](https://github.com/snototter/iminspect/blob/master/screenshots/mask.jpg?raw=true "iminspect GUI")

Example: visualizing optical flow<br/>
![Screenshot optical flow](https://github.com/snototter/iminspect/blob/master/screenshots/flow-uv.jpg?raw=true "iminspect GUI")


## UI Documentation
* To inspect a data point/pixel, just move the mouse above it.
* Zooming:
  * `Ctrl+Wheel` to zoom in/out.
  * `Ctrl+Shift+Wheel` to speed up zooming.
  * `Ctrl+{+|-}` to zoom in/out.
  * `Ctrl+Shift+{+|-}` to zoom in/out faster.
  * `Ctrl+F` zoom such that image fills the available canvas.
  * `Ctrl+1` zoom to original size.
* Scrolling:
  * `Wheel` scroll up/down.
  * `Shift+Wheel` speeds up scrolling.
  * `Ctrl+{Up|Down|Left|Right}` to scroll using keyboard.
  * `Ctrl+Shift+{Up|Down|Left|Right}` scrolls faster.
* Keyboard shortcuts:
  * `Ctrl+Q` closes the inspection GUI.
  * `Ctrl+O` shows dialog to open another file.
  * `Ctrl+S` shows dialog to save input or visualization data.


## Changelog
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


## Upcoming Changes/Known Issues
* Usability: Incrementally in-/decreasing the zoom factor worked "good enough" so far, however, "fast zooming" seems a bit "too fast" at times (especially for smaller input images).
* Issue: Initial window resize won't scale to the exact specified size (additionally, QApplication...processEvents() won't finish resizing - image canvas widget will be resized "shortly" after a second time)
* Feature: Implement a range slider to change visualization limits on-the-fly.
* Feature: Extend flow visualization, i.e. if data is a rgb/flow tuple, show both next to each other.
  * Zoom/scroll actions should be linked.
  * Tool tips should show on both viewers.

