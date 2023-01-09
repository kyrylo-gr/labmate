# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 16:36:40 2023

@author: CryoPc
"""
import sys

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtGui import QFileOpenEvent

import h5py


class CentralWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CentralWidget, self).__init__(parent)
        self.lay = QtWidgets.QVBoxLayout()
        self.setLayout(self.lay)
        
        

class EditorWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(EditorWindow, self).__init__(parent)
        self.central_widget = CentralWidget(self)
        self.text_edit = QtWidgets.QTextEdit()

        self.setCentralWidget(self.text_edit)
        self.combo = QtWidgets.QComboBox()
        self.setMenuWidget(self.combo)
        self.combo.currentIndexChanged.connect(self.item_changed)
        
        self.file_path = None
        
        #self.combo.addItem("Nothing to display")
        
    def item_changed(self):
        with h5py.File(self.file_path, 'r') as f:
            self.text_edit.setText(str(f[self.combo.currentText()][()]))
        
    def set_default_key(self):
        self.combo.setCurrentText("acquisition_cell")
        
    def open_file(self, file_path):
        self.file_path = file_path
        set_default = self.combo.currentIndex()==-1
        self.combo.clear()
        with h5py.File(file_path, 'r') as f:
            for key in f.keys():
                self.combo.addItem(key)
        if set_default:
            self.set_default_key()
        
        

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