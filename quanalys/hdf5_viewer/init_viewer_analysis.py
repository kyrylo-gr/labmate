# flake8: noqa # type: ignore # pylint: skip-file
import qm_utils
import analysis
import matplotlib.pyplot as plt
import numpy as np

import sys
from tqdm import tqdm
from quanalys.acquisition_notebook import AcquisitionNotebookManager
from quanalys.acquisition_utils import AcquisitionLoop

sys.path.append(r"C:\Users\CryoPc\Documents\GitHub\mecaflux\notebooks\cooldowns\2023_01_06_CEAv1_die8")

aqm = AcquisitionNotebookManager(r"C:\Users\CryoPc\My Drive\mecaflux\measurements\Cooldown_2023_01_06_CEAv1_die8\\")
