# encoding: utf-8
import winreg
import subprocess
import sys
import os

sys.path.append('../ifc')
from ifc import ifcproject
from dataclasses import dataclass
from .widgets import *
from .loaders import *
from .ui import *
from .models import *

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Project params to generate the IFC file
        self.__structureSettings = ifcproject.StructureSettings()
        self.__roofSettings      = ifcproject.RoofSettings()
        self.__regionSettings    = ifcproject.RegionSettings()
        self.__materialSettings  = ifcproject.MaterialSettings()

        # Load PyQt UI and widgets
        self.__ui = Ui_MainWindow()
        self.__ui.setupUi(self)

        self.__InitWidgets()

    def __InitWidgets(self):
        doubleValidator = QDoubleValidator()
        
        # Configurations
        self.__ui.configGroupWidthLineEdit.setValidator(doubleValidator)
        self.__ui.configGroupLengthLineEdit.setValidator(doubleValidator)
        self.__ui.configGroupFloorLineEdit.setValidator(doubleValidator)
            
        # Roof 
        self.__ui.roofGroupSettingsWidget.setEnabled(False)
        self.__ui.roofGroupEditCheckBox.stateChanged.connect(lambda: self.__ui.roofGroupSettingsWidget.setEnabled(self.__ui.roofGroupEditCheckBox.isChecked()))
        
        self.__ui.roofGroupAngleLineEdit.setValidator(doubleValidator)
        self.__ui.roofGroupWeightLineEdit.setValidator(doubleValidator)
        self.__ui.roofGroupDistanceLineEdit.setValidator(doubleValidator)

        roofDataModel = RoofDataModel(self.__ui.roofGroupAngleLineEdit,
                                      self.__ui.roofGroupWeightLineEdit,
                                      self.__ui.roofGroupDistanceLineEdit,
                                      dataSelector = self.__ui.roofGroupTileComboBox,
                                      data = LoadJSON("src/data/rooftile.json"))

        # States
        stateDataModel = StateDataModel(dataSelector = self.__ui.regionGroupStateComboBox,
                                        displayList = self.__ui.regionGroupListWidget,
                                        data = LoadJSON("src/data/states.json"))
        
        # Materials
        materialDataModel = MaterialDataModel(dataSelector = self.__ui.materialGroupTypeComboBox,
                                              layout = self.__ui.materialGroupMainLayout,
                                              data = LoadJSON("src/data/materials.json"))
        
        # Generate
        self.__ui.generateButton.clicked.connect(self.__GenerateProject)

    def __GetUserInput(self):
        GetTextInput = lambda widget, default: widget.text() if widget.text() else default

        self.__structureSettings.width  = float(GetTextInput(self.__ui.configGroupWidthLineEdit,  self.__structureSettings.width))
        self.__structureSettings.length = float(GetTextInput(self.__ui.configGroupLengthLineEdit, self.__structureSettings.length))
        self.__structureSettings.floors =   int(GetTextInput(self.__ui.configGroupFloorLineEdit,  self.__structureSettings.floors))

    def __GenerateProject(self):
        self.__GetUserInput()

        # Generate the IFC project
        project = ifcproject.Project(structureSettings=self.__structureSettings)
        project.GenerateIFCFile("projeto")

        # Run DDS-CAD Viewer
        try:
            ddsCadViewerRegKey = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\DdsViewer.exe")
            ddsCadViewerPath = winreg.QueryValueEx(ddsCadViewerRegKey, None)[0]
            subprocess.run([ddsCadViewerPath, 'build\\projeto.ifc'])
        except OSError:
            msg = QMessageBox()
            msg.setWindowTitle('Erro ao abrir o arquivo!')
            msg.setText("Não foi possível encontrar um caminho de instalação válido para o programa 'DDS-CAD Viewer'. Instale o programa recomendado ou procure uma alternativa de software para a visualização de arquivos de formato '.ifc'.")
            msg.setIcon(QMessageBox.Warning)
            msg.exec_()
  
        '''
        # RUN BIM-Vision Viewer
        try: 
            bimVisionViewerRegKey = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, r"\SOFTWARE\\Classes\\BIMvision\\shell\\open\\command")
            bimVisionViewerPath = winreg.QueryValueEx(bimVisionViewerRegKey,None)[0]
            print(bimVisionViewerPath)
            subprocess.run([bimVisionViewerPath,'projeto.ifc'])
        except OSError: 
          msg = QMessageBox()
          msg.setWindowTitle('Erro ao abrir o arquivo!')
          msg.setText("Não foi possível encontrar um caminho de instalação válido para o programa 'Bim_Vision Viewer'. Instale o programa recomendado ou procure uma alternativa de software para a visualização de arquivos de formato '.ifc'.")
          msg.setIcon(QMessageBox.Warning)
          msg.exec_()
        '''