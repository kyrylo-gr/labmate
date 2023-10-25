"""Load autoreload extension to ipython.

Instead:
```
%load_ext autoreload
%autoreload 2
```

Run:
```
import labmate.utils.autoreload
```

"""
from IPython.core.getipython import get_ipython

shell = get_ipython()
if shell:
    shell.run_cell("%load_ext autoreload")
    shell.run_cell("%autoreload 2")
