# iminspect
A python utility package for image/matrix visualization.

## Dependencies
* `numpy`, obviously
* `PyQt5` for the graphical user interface
* `qimage2ndarray` to convert numpy ndarrays to Qt images

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
  * Additionally holding `Shift` speeds up zooming
* Scrolling
  * Move the scroll bars
  * `Wheel` up/down
  * Additionally holding `Shift` speeds up scrolling

## Changelog
* `0.1.1`
  * Additional features:
    * ImageCanvas supports ROI selection (useful for custom input widgets)
  * Refactoring:
    * Clean up imports
    * Make pylint/flake8 happier
  * Fixes:
    * Adjust scrollbars when zooming multiple linked ImageCanvas
* `0.1.0` - Initial public release

