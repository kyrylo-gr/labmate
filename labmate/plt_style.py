import matplotlib.pylab as plt
from cycler import cycler

colors = ['#0066cc', '#ffcc00', '#ff7400', '#962fbf', '#8b5a2b',
          '#d62976', '#b8a7ea', '#ed5555', '#1da2d8']

plt.rcParams.update({
    'font.size': 14,
    'axes.titlesize': 14,
    'axes.labelsize': 14,
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'legend.fontsize': 14,
    'figure.titlesize': 14,
    'axes.prop_cycle': cycler('color', colors)
})


size_dict = {
    "large": (12, 8),
    "normal": (9, 6),
    "small": (6, 4),
}


def subplots(*args, size="normal", **kwds):
    if 'figsize' not in kwds:
        kwds['figsize'] = size_dict[size]
    return plt.subplots(*args, **kwds)


def figure(*args, size="normal", **kwds):
    if 'figsize' not in kwds:
        kwds['figsize'] = size_dict[size]
    return plt.figure(*args, **kwds)


# 4 3
# 8 6
# 11 6
