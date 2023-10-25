# pylint: disable=wrong-import-order, wrong-import-position, unused-import
# flake8: noqa
# SOURCE: source ~/opt/anaconda3/bin/activate phd_mask

import sys
import os
import matplotlib.pylab as plt
from labmate.acquisition_notebook import AcquisitionAnalysisManager
from dh5.path import Path

SCRIPT_DIR = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(os.path.join(os.path.abspath(SCRIPT_DIR), "analyse"))
meas_dir = Path(SCRIPT_DIR).parent.parent.parent
aqm = AcquisitionAnalysisManager(meas_dir)

print("init_analysis")
