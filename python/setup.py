"""
Package creation script
"""
# How to: https://packaging.python.org/tutorials/packaging-projects/
# * Build package
#   pip install --upgrade setuptools wheel
#   python setup.py sdist bdist_wheel
# * Upload to TestPyPI
#   pip install --upgrade twine
#   python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
# * Test installation
#   pip install --index-url https://test.pypi.org/simple/ --no-deps iminspect-snototter

import setuptools

# Load description
with open('README.md', 'r') as fr:
    long_description = fr.read()

# Load version string
loaded_vars = dict()
with open('iminspect/version.py') as fv:
    exec(fv.read(), loaded_vars)

setuptools.setup(
    name="iminspect",
    version=loaded_vars['__version__'],
    author="snototter",
    author_email="muspellr@gmail.com",
    description="Qt-based GUI to visualize image-like data.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/snototter/iminspect",
    packages=setuptools.find_packages(),
    install_requires=[
        'numpy',
        'PyQt5',
        'qimage2ndarray'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
