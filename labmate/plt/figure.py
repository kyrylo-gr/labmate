import matplotlib.pylab as plt


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
