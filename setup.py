"""
Package creation script

How to packaging:
https://packaging.python.org/tutorials/packaging-projects/

From the python3 virtualenv:
pip install --upgrade setuptools wheel
python setup.py sdist bdist_wheel
pip install --upgrade twine
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
twine upload dist/*
"""

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
        'qimage2ndarray',
        'vito>=1.1.4'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)
