from .data_structure import AcquisitionLoop, AcquisitionManager, \
                            acquisition_cell, analysis_cell, AnalysisManager


def save_acquisition(**kwds):
    acq = AcquisitionManager.get_ongoing_acquisition()
    acq.add_kwds(**kwds)
    acq.save_config_files()
    acq.save_cell()
    acq.save_data()
    AcquisitionManager._last_acquisition_saved = True

def load_acquisition():
    return AnalysisManager.current_analysis