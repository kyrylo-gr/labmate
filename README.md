# Labmate. The mate that simplifies data management in your lab.

<h1 align="center">
<img src="docs/images/labmate-preview.png" width="600">
</h1><br>

<div align="center">

[![Pypi](https://img.shields.io/pypi/v/labmate.svg)](https://pypi.org/project/labmate/)
![Python 3.7+](https://img.shields.io/badge/python-3.7%2B-blue)
[![License](https://img.shields.io/badge/license-LGPL-green)](./LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CodeFactor](https://www.codefactor.io/repository/github/kyrylo-gr/labmate/badge/main)](https://www.codefactor.io/repository/github/kyrylo-gr/labmate/overview/main)
[![Codecov](https://codecov.io/gh/kyrylo-gr/labmate/graph/badge.svg)](https://codecov.io/gh/kyrylo-gr/labmate)
[![Download Stats](https://img.shields.io/pypi/dm/labmate)](https://pypistats.org/packages/labmate)
[![Documentation](https://img.shields.io/badge/docs-blue)](https://kyrylo-gr.github.io/labmate/)

</div>

This library facilitates the clear division of data acquisition from analysis. It provides robust tools for efficient data management and includes features to ensure a further use of the saved data.

This library is based on the other library [dh5](https://kyrylo-gr.github.io/dh5/) which is a wrapper around the h5py library.

## Install

`pip install labmate`

## Installation in dev mode

`pip install -e .[dev]` or `python setup.py develop`

## Usage

Setup:

```python
from labmate.acquisition_notebook import AcquisitionAnalysisManager
aqm = AcquisitionAnalysisManager("path/to/database")
```

Example of an acquisition cell. The variables x and y, along with the acquisition cell code and additional parameters that can be set, will be saved inside an h5 file.

```python
aqm.acquisition_cell("your_experiment_name")
...
aqm.save_acquisition(x=x, y=y)
```

Example of an analysis cell. You cannot directly use the `x` or `y` variables, as you would not be able to open them afterwards. Therefore, whenever you use variables inside an analysis cell, retrieve them from `aqm.data`.

```python
aqm.analysis_cell()

data = aqm.data
fig, ax = plt.subplots(1, 1)
ax.plot(data.x, data.y)

aqm.save_fig(fig)
```

You can find this example [here](https://github.com/kyrylo-gr/labmate/blob/main/docs/examples/aqm_simple_example.ipynb).

## More usage

To see more look at [the documentation](https://kyrylo-gr.github.io/labmate/)
