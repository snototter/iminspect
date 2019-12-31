# iminspect
[![View on PyPI](https://img.shields.io/pypi/v/iminspect.svg)](https://pypi.org/project/iminspect)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/snototter/iminspect/blob/master/LICENSE?raw=true)

A python utility package for image/matrix visualization.

## Dependencies
* `numpy`, obviously
* `PyQt5` for the graphical user interface
* `qimage2ndarray` to convert numpy ndarrays to Qt images
* `vito` a lightweight vision tool package

## Example usage:
```python
from iminspect.inspector import inspect
import numpy as np

# Show random noise image:
inspect(np.random.rand(4096,4096) - 0.5)

# Show as class labels:
inspect((np.random.rand(16,16) * 1e2 % 5).astype(np.int16), is_categoric=True)
```

Exemplary screenshot (visualizing categoric data, i.e. labels):<br/>
![Screenshot](https://github.com/snototter/iminspect/blob/master/iminspect.jpg?raw=true "iminspect GUI")


## UI Documentation
* To inspect a data point/pixel, just move the mouse above it.
* Zooming
  * `Ctrl+Wheel` to zoom in/out
  * `Ctrl+Shift+Wheel` to speed up zooming
  * `Ctrl+{+|-}` to zoom in/out
  * `Ctrl+Shift+{+|-}` to zoom in/out faster
* Scrolling
  * `Wheel` scroll up/down
  * `Shift+Wheel` speeds up scrolling
  * `Ctrl+{Up|Down|Left|Right}` to scroll using keyboard
  * `Ctrl+Shift+{Up|Down|Left|Right}` scrolls faster
* Keyboard shortcuts
  * `Ctrl+Q` closes the inspection GUI


## Changelog
* `0.2.0`
  * Major refactoring: moved image utils and colorizing code to separate [vito](https://github.com/snototter/vito) package
  * Usability improvements: keyboard shortcuts for zooming, scaling and scrolling
* `0.1.2`
  * Added tests for non-GUI functionality
  * Integrate github runners for test/build/deploy
  * Fix definition for colormap gray
* `0.1.1`
  * Additional features:
    * ImageCanvas supports ROI selection (useful for custom input widgets)
  * Refactoring:
    * Clean up imports
    * Make pylint/flake8 happier
  * Fixes:
    * Adjust scrollbars when zooming multiple linked ImageCanvas
* `0.1.0` - Initial public release


## Upcoming Changes
* [ ] Support flow visualization<br/>2-layer flow, default to color wheel representation, port C++/MATLAB https://people.csail.mit.edu/celiu/OpticalFlow/
* [ ] Add load from disk functionality
