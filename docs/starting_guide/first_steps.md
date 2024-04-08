# Getting Started with Labmate

Make sure you have [installed the package](install.md) before.

## Overview

Easily we can divide classical scientific experiment to acquisition of some data and analysis of this data. An acquisition is something that is run ones to get nice data and then you'd like to analyze it. `Labmate` library also separates these two stage and protects the data during an analysis by using read-only access to the data.

During this tutorial we start with the simple experimental sequence, and then see which features `labmate` to improve you experience and assure the further reuse of your data.

## Simple example

As mentioned above every experimental sequence consists of 2 steps: acquisition and analysis.

### Setup

Before starting performing the experiment you should defined AcquisitionAnalysisManager. It's super simple: you import it and give it an directory where to save your data.

```python
from labmate.acquisition_notebook import AcquisitionAnalysisManager

aqm = AcquisitionAnalysisManager("tmp_data")
# this would save data inside /path/to/current/file/tmp_data/
```

### Acquisition cell

Acquisition cell is a notebook cell that performs the experiment and saves the results. It should start with `acquisition_cell` method.

```python
aqm.acquisition_cell('test_example')

# acquire data. Here is an example of simple sinusoidal data.
x = np.linspace(0, 20*np.pi, 101)
your_data = np.sin(x)

# Save data to the file.
aqm.save_acquisition(x=x, y=your_data)
```

### Analysis data

Analyze of data starts by `analysis_cell`.
During your analysis, you should never uses variable outside of your saved date. To assure this, you should access variables via `aqm.data`.

```python
aqm.analysis_cell()

fig = plt.figure()
plt.plot(aqm.data.x, aqm.data.y)
aqm.save_fig(fig)
```

## Further Details

To learn even more about how dh5 is structured, explore the [Advanced Examples](advanced_examples.md).
