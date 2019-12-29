import setuptools

with open('README.md', 'r') as fr:
    long_description = fr.read()

setuptools.setup(
    name="iminspect",
    version="0.1.0",
    author="snototter",
#    author_email="TBD",
    description="Qt-based GUI to visualize image-like data for faster python prototyping.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/snototter/iminspect",
    packages=setuptools.find_packages(),
    install_requires=['numpy', 'Pillow', 'PyQt5', 'qimage2ndarray'],
    license='MIT',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
