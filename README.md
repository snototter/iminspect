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
  * Press and move left/right button to drag the image if zoomed in.
* Keyboard shortcuts:
  * `Ctrl+Q` and `Ctrl+W` closes the inspection GUI.
  * `Ctrl+O` shows dialog to open another file.
  * `Ctrl+S` shows dialog to save input or visualization data.
  * `Ctrl+T` toggle tool tip display when moving the mouse over the data.


## Changelog
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

