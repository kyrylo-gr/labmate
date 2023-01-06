from IPython import get_ipython

shell = get_ipython()
if shell:
    shell.run_cell("%load_ext autoreload")
    shell.run_cell("%autoreload 2")
