# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 16:36:40 2023

@author: CryoPc
"""
import sys, os
import IPython

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtGui import QFileOpenEvent

import h5py
import os.path as osp


class CentralWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CentralWidget, self).__init__(parent)
        self.lay = QtWidgets.QVBoxLayout()
        self.text_edit = QtWidgets.QTextEdit()
        self.lay.addWidget(self.text_edit)
        self.run_analysis_button = QtWidgets.QPushButton("Run analysis")
        self.lay.addWidget(self.run_analysis_button)
        self.setLayout(self.lay)
        
    
class EditorWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(EditorWindow, self).__init__(parent)
        self.central_widget = CentralWidget(self)
        self.text_edit = self.central_widget.text_edit
        self.run_analysis_button = self.central_widget.run_analysis_button
        self.run_analysis_button.clicked.connect(self.run_analysis)


        self.setCentralWidget(self.central_widget)
        self.combo = QtWidgets.QComboBox()
        self.setMenuWidget(self.combo)
        self.combo.currentIndexChanged.connect(self.item_changed)
        
        self.file_path = None
        
        #self.combo.addItem("Nothing to display")

    def run_analysis(self):
        with h5py.File(file_path, 'r') as f:
            analysis_code_original = self.text_edit.toPlainText()
        with open(osp.join(osp.split(osp.abspath(__file__))[0], "init_viewer_analysis.py"), 'r') as f:
            init_code = f.read()
        #os.chdir(r"C:\Users\CryoPc\Documents\GitHub\mecaflux\notebooks\cooldowns\2023_01_06_CEAv1_die8")

        analysis_code = analysis_code_original.replace("%", "#%")
        analysis_code = analysis_code.replace("aqm.analysis_cell(", f"aqm.analysis_cell(r'{file_path}', cell=__the_cell_content__)\n#aqm.analysis_cell(")

        exec(init_code + '\n'  + analysis_code, dict(__the_cell_content__=analysis_code_original))
        #with h5py.File(file_path, 'w') as f:
        #    f["analysis_cell"] = self.text_edit.toPlainText()

    def item_changed(self):
        with h5py.File(self.file_path, 'r') as f:
            if self.combo.currentText() in f.keys():
                self.text_edit.setText(str(f[self.combo.currentText()][()]))
            else:
                self.text_edit.setText("")
        self.set_button_visibility()

    def set_button_visibility(self):
        visibility = self.combo.currentText()=="analysis_cell"
        self.run_analysis_button.setVisible(visibility)
        
    def set_default_key(self):
        self.combo.setCurrentText("acquisition_cell")
        self.combo.setCurrentText("analysis_cell") # if existing, pick this one

    def open_file(self, file_path):
        self.file_path = file_path
        set_default = self.combo.currentIndex()==-1
        self.combo.clear()

        with h5py.File(file_path, 'r') as f:
            def depth_first_search(key, obj, all_items=[]):
                if hasattr(obj, "keys"):
                    for child_key in obj.keys():
                        depth_first_search(key + '/' + child_key, obj[child_key], all_items)
                else:
                    all_items.append([key.lstrip("/"), obj])
                return all_items

            items = depth_first_search("", f)
            for key, value in items:
                self.combo.addItem(key)
            if not "analysis_cell" in f.keys():
                self.combo.addItem("analysis_cell")
        
        if set_default:
            self.set_default_key()
        
        self.setWindowTitle(osp.split(file_path)[1])
        self.resize(500, 600)
        

#class FileOpenEventHandler(QtWidgets.QApplication):
#    def event(self, event):
#        if event.type() == QFileOpenEvent.FileOpen:
#            file_path = event.file()
#            print(f'A file was opened: {file_path}')
#        return super().event(event)

#APP = FileOpenEventHandler(sys.argv)
APP = QtWidgets.QApplication(sys.argv)
EDITOR = EditorWindow(None)
EDITOR.show()

#%%

if __name__=="__main__":
    
    if len(sys.argv)>1:
        file_path = sys.argv[1] 
        EDITOR.open_file(file_path)

    APP.exec_()