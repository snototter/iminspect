# iminspect

Utils to quickly visualize image-like data to allow faster-paced development.

Example usage of python package:
```python
from iminspect.inspector import inspect as inspect
import numpy as np

# Show as class labels:
inspect((np.random.rand(16,16) * 1e2 % 5).astype(np.int16), is_categoric=True)

# Random noise:
inspect(np.random.rand(4096,4096))
```

Exemplary screenshot, visualizing categoric data (i.e. class labels):
![Screenshot](./python/iminspect.jpg "Screenshot")

To be done:
* c++ port (leverage OpenCV UI 'capabilities' instead of qt)
* include additional pvt3 functionality (e.g. ROI selection widget)
* refactor (qt vs. custom naming schema)

