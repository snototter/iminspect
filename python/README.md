# iminspect
A `python3` utility package for image/matrix visualization.

## Dependencies
* `PyQt5` for the graphical user interface
* `qimage2ndarray` to convert numpy ndarrays to Qt images
* `numpy`, obviously

## Example usage:
```python
from iminspect.inspector import inspect as inspect
import numpy as np

# Show as class labels:
inspect((np.random.rand(16,16) * 1e2 % 5).astype(np.int16), is_categoric=True)

# Random noise:
inspect(np.random.rand(4096,4096))
```

## UI Documentation
* Zooming
  * `Ctrl+Wheel` to zoom in/out
  * Additionally holding `Shift` speeds up zooming
* Scrolling
  * Move the scroll bars
  * `Wheel` up/down
  * Additionally holding `Shift` speeds up scrolling
* Value at the cursor position will be displayed as tool tip and within the status bar
