import matplotlib.pylab as plt
from cycler import cycler

from .style import colors

plt.rcParams.update(
    {
        'font.size': 14,
        'axes.titlesize': 14,
        'axes.labelsize': 14,
        'xtick.labelsize': 14,
        'ytick.labelsize': 14,
        'legend.fontsize': 14,
        'figure.titlesize': 14,
        'axes.prop_cycle': cycler('color', colors),
    }
)
