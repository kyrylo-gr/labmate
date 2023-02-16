# -*- coding: utf-8 -*-
"""
@author: Samuel Deleglise

All questions to the author.
"""
import ctypes
import sys
import os
import traceback

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QStyle

import h5py
import os.path as osp


class CentralWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lay = QtWidgets.QVBoxLayout()
        self.text_edit = QtWidgets.QTextEdit()
        self.lay.addWidget(self.text_edit)
        self.run_analysis_button = QtWidgets.QPushButton("Run analysis")
        self.lay.addWidget(self.run_analysis_button)
        self.setLayout(self.lay)


class EditorWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.central_widget = CentralWidget(self)
        self.text_edit = self.central_widget.text_edit
        self.run_analysis_button = self.central_widget.run_analysis_button
        self.run_analysis_button.clicked.connect(self.run_analysis)

        self.setCentralWidget(self.central_widget)
        self.combo = QtWidgets.QComboBox()
        self.setMenuWidget(self.combo)
        self.combo.currentIndexChanged.connect(self.item_changed)

        self.icon = self.style().standardIcon(QStyle.SP_DriveFDIcon)  # type: ignore
        self.setWindowIcon(self.icon)

        self.file_path = None

        #self.combo.addItem("Nothing to display")

    def find_code_dir(self):
        """
        A source code directory with analysis scripts is conventionally located in measurement_dir/code
        """
        measurement_dir = self.find_measurement_dir()
        return osp.join(measurement_dir, 'code')

    def find_measurement_dir(self):
        assert self.file_path, "normally find_code_dir runs after open_file. It wasn't the case now"
        return osp.split(osp.split(self.file_path)[0])[0]

    def run_analysis(self):
        code_dir = self.find_code_dir()
        if osp.exists(code_dir):
            os.chdir(code_dir)
            sys.path.append(code_dir)

        analysis_code_original = self.text_edit.toPlainText()
        measurement_dir = self.find_measurement_dir()
        init_code = f"""try:
    from init_notebook import *
except ModuleNotFoundError:
    from labmatequisition_notebook import AcquisitionAnalysisManager
    measurement_dir = r"{measurement_dir}"
    import matplotlib.pyplot as plt
    aqm = AcquisitionAnalysisManager(measurement_dir)
    print("init_notebook wasn't found, skipping import...")"""

        analysis_code = analysis_code_original.replace("%", "#%")
        analysis_code = analysis_code.replace(
            "aqm.analysis_cell(",
            f"aqm.analysis_cell(r'{self.file_path}', cell=__the_cell_content__)\n#aqm.analysis_cell(")
        try:
            exec(init_code + '\n' + analysis_code,  # pylint: disable=W0122
                 dict(__the_cell_content__=analysis_code_original))
        except Exception:
            print(traceback.format_exc())

        # with h5py.File(file_path, 'w') as f:
        #    f["analysis_cell"] = self.text_edit.toPlainText()

    @property
    def filename(self):
        if self.file_path is None:
            raise ValueError("There is no file_path specified. Should open_file first")
        return os.path.split(self.file_path)[-1]

    def replace_analysis_cell_statement(self, value):
        return "\n".join([line if not line.startswith("aqm.analysis_cell(")
                          else f'aqm.analysis_cell("{self.filename}")'
                          for line in value.split("\n")])

    def item_changed(self):
        key = self.combo.currentText()
        with h5py.File(self.file_path, 'r') as file:
            if key in file.keys():
                value = str(file[key][()])  # type: ignore
                if key == "analysis_cell":
                    value = self.replace_analysis_cell_statement(value)
                self.text_edit.setText(value)
            else:
                if key == "analysis_cell":
                    value = f'aqm.analysis_cell("{self.filename}")\n'
                else:
                    value = ""
                self.text_edit.setText(value)
        self.set_button_visibility()

    def set_button_visibility(self):
        visibility = self.combo.currentText().startswith("analysis_cell")
        self.run_analysis_button.setVisible(visibility)

    def set_default_key(self):
        self.combo.setCurrentText("acquisition_cell")
        index = self.combo.findText('analysis_cell')
        key = self.combo.itemText(index)
        #analysis_keys = [key for key in self.combo.keys() if key.startswith('analysis_cell')]
        # if len(analysis_keys)>0:
        self.combo.setCurrentText(key)  # if existing, pick this one

    def open_file(self, file_path):
        self.file_path = file_path
        set_default = self.combo.currentIndex() == -1
        self.combo.clear()

        with h5py.File(file_path, 'r') as f:
            for key in allkeys(f):
                self.combo.addItem(key)
            if "analysis_cell" not in f.keys():
                self.combo.addItem("analysis_cell")

        if set_default:
            self.set_default_key()

        self.setWindowTitle(osp.split(file_path)[1])
        self.resize(500, 600)


def allkeys(obj):
    "Recursively find all keys in an h5py.Group."
    keys = []
    if isinstance(obj, h5py.Group):
        for key, value in obj.items():
            if isinstance(value, h5py.Group):
                keys = keys + allkeys(value)
            else:
                keys = keys + [value.name, ]
    return [key.lstrip("/") for key in keys]


# class FileOpenEventHandler(QtWidgets.QApplication):
#    def event(self, event):
#        if event.type() == QFileOpenEvent.FileOpen:
#            file_path = event.file()
#            print(f'A file was opened: {file_path}')
#        return super().event(event)


# Apparently needed for the icon
app_id = 'lkb.OMQ.quanalys.1'  # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)  # type: ignore


#APP = FileOpenEventHandler(sys.argv)
APP = QtWidgets.QApplication(sys.argv)
EDITOR = EditorWindow(None)
APP.setWindowIcon(EDITOR.icon)  # Not sure if needed
EDITOR.show()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        FILE_PATH = sys.argv[1]
        EDITOR.open_file(FILE_PATH)
    APP.exec_()
