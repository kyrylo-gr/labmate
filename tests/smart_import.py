# pylint: disable=wrong-import-order, wrong-import-position, unused-import
# flake8: noqa

print("Kernel is started")

import os
import sys

def add_parent_dir_to_path():
    SCRIPT_DIR = os.path.join(os.path.dirname( __file__ ), os.pardir)
    sys.path.append(os.path.abspath(SCRIPT_DIR))
    
try:
    import acquisitionutils
except ModuleNotFoundError:
    add_parent_dir_to_path()
