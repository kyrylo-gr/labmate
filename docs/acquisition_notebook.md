# Acquisition notebook

`Acquisition_notebook` package is helping for saving the data of your analysis.

## Import

```python
from labmate.acquisition import AcquisitionManager, save_acquisition, load_acquisition, AcquisitionLoop, AnalysisManager
from labmate.acquisition_notebook import acquisition_cell
```

## Simple case

You have 2 cells. First run the measurements, second perform the analysis. Then in the beginning of the first cell you write `%%acquisition_cell name_of_experiment` and in the second one `%%analysis_cell`. In `acquisition_cell` you should save you data by calling `save_acquisition(x=x, y=y)` function. And in `analysis_cell` you can get you data by calling the `load_acquisition` function.

### Example

Cell 1:

```python
%%acquisition_cell saving_sine2

x = np.linspace(0, 20*np.pi, 101)
y = np.sin(x)
save_acquisition(x=x, y=y)
```

Cell 2:

```python
%%analysis_cell
from pylab import *

data = load_acquisition()
fig = plt.figure()
plt.plot(data.x, data.y)

data.save_fig(fig)
```
