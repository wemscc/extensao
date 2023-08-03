# encoding: utf-8
import typing
from PyQt5 import QtCore
from PyQt5.QtCore import QModelIndex, QObject, Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QWidget

from functools import partial
from enum import Enum

class MaterialWidgetFactory:
    MaterialType = Enum('Materials', 'Wood Steel')

    @staticmethod
    def CreateWidget(data):
        materialType = MaterialWidgetFactory.MaterialType[data.get("type")]

        match(materialType):
            case MaterialWidgetFactory.MaterialType.Wood:
                return WoodMaterialWidget(data)
            case MaterialWidgetFactory.MaterialType.Steel:
                return SteelMaterialWidget(data)
            case _:
                print("Material Widget Factory - Invalid type of material passed. Cannot create widget.")


class WoodMaterialWidget(QWidget):
    class TableModel(QAbstractTableModel):
        def __init__(self, data) -> None:
            super().__init__()
            self.__data = data
            self.__rowHeader    = ["fbk", "ft0k", "ft90k", "fc0k", "fc90k", "fvk", "E0m", "E005", "E90m", "Gm", "pk", "pm"]
            self.__columnHeader = ["Atributos"]

        def data(self, index, role):
            if role == Qt.DisplayRole:
                return self.__data[index.row()][index.column()]
            if role == Qt.TextAlignmentRole:
                return Qt.AlignHCenter

        def rowCount(self, index):
            return len(self.__rowHeader)
        
        def columnCount(self, index):
            return len(self.__columnHeader)

        def setData(self, index, value):
            self.__data[index.row()][index.column()] = value
            self.dataChanged.emit(index, index)
            return True

        def headerData(self, section, orientation, role):
            if role == Qt.DisplayRole:
                if orientation == Qt.Vertical:
                    return self.__rowHeader[section]
                if orientation == Qt.Horizontal:
                    return self.__columnHeader[section]

    def __init__(self, data = {}) -> None:
        super().__init__()
        self.__data = data

        # Create child widgets, but do not initialize
        self.__CreateChildWidgets()

        # Classes
        self.__class = self.__data.get("class")
        self.__classViewModel = QStringListModel([entry.get("class") for entry in self.__class.values()])
        self.__classComboBox.setModel(self.__classViewModel)

        # Names
        self.__names = [entry.get("name") for entry in self.__class.values()]
        self.__namesModel = QStringListModel(self.__names)
        self.__completer = QCompleter()
        self.__completer.setModel(self.__namesModel)
        self.__nameLineEdit.setCompleter(self.__completer)

        # Attributes
        self.__attributes = [entry.get("attributes") for entry in self.__class.values()]

        # Load the attributes from the first selected class
        att = [[value] for value in self.__attributes[self.__classComboBox.currentIndex()].values()]
        self.__attributesViewModel = WoodMaterialWidget.TableModel(att)
        
        # Handler for the selector
        self.__classComboBox.currentIndexChanged.connect(self.__SelectClass)

        # Handler for the search bar
        self.__nameLineEdit.editingFinished.connect(self.__SearchByName)

        # With everything set up, initialize child widgets
        self.__InitChildWidgets()

    def __SelectClass(self):
        classAttributes = [att for att in self.__attributes[self.__classComboBox.currentIndex()].values()]
        for i, value in enumerate(classAttributes):
            self.__attributesViewModel.setData(self.__attributesViewModel.index(i, 0), value)

    def __SearchByName(self):
        name = self.__nameLineEdit.text()

        if name not in self.__names:
            return

        idx = self.__names.index(name)
        classAttributes = [att for att in self.__attributes[idx].values()]
        for i, value in enumerate(classAttributes):
            self.__attributesViewModel.setData(self.__attributesViewModel.index(i, 0), value)

    # TODO: REFACTOR (HARDCODED!)
    def __CreateChildWidgets(self):
        # Search by class
        self.__classWidget     = QWidget(self)
        self.__classLabel      = QLabel(self.__classWidget)
        self.__classComboBox   = QComboBox(self.__classWidget)
        self.__classToolButton = QToolButton(self.__classWidget)
        self.__classLayout     = QHBoxLayout(self.__classWidget)

        # Search by name
        self.__nameWidget     = QWidget(self)
        self.__nameLabel      = QLabel(self.__nameWidget)
        self.__nameLineEdit   = QLineEdit(self.__nameWidget)
        self.__nameToolButton = QToolButton(self.__nameWidget)
        self.__nameLayout     = QHBoxLayout(self.__nameWidget)

        # Table view
        self.__tableWidget = QTableView(self)

        # Main layout
        self.__mainLayout = QVBoxLayout()

    # TODO: REFACTOR (HARDCODED!)
    def __InitChildWidgets(self):
        # Search by class
        self.__classLabel.setText("Classe")
        self.__classComboBox.setFixedSize(50, 20)
        self.__classToolButton.setIcon(QIcon("./assets/imgs/gear.png"))
        self.__classToolButton.setToolTip("Procurar o tipo de madeira por nome")
        self.__classLayout.addWidget(self.__classLabel)
        self.__classLayout.addWidget(self.__classComboBox)
        self.__classLayout.addWidget(self.__classToolButton)
        self.__classLayout.setContentsMargins(0, 0, 0, 0)

        # Search by name
        self.__nameLabel.setText("Nome")
        self.__nameLineEdit.setFixedSize(150, 20)
        self.__nameLineEdit.setPlaceholderText("Procurar por nome")
        self.__nameLineEdit.setAlignment(Qt.AlignCenter)
        self.__nameLineEdit.setValidator(QRegExpValidator(QRegExp("[A-Za-z0-9]{0,20}")))
        self.__nameToolButton.setIcon(QIcon("./assets/imgs/gear.png"))
        self.__nameToolButton.setToolTip("Procurar o tipo de madeira por classe")
        self.__nameLayout.addWidget(self.__nameLabel)
        self.__nameLayout.addWidget(self.__nameLineEdit)
        self.__nameLayout.addWidget(self.__nameToolButton)
        self.__nameLayout.setContentsMargins(0, 0, 0, 0)

        # Table view
        self.__tableWidget.setModel(self.__attributesViewModel)
        self.__tableWidget.setStyleSheet("font-size: 10px;")
        self.__tableWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.__tableWidget.setFocusPolicy(Qt.NoFocus)
        self.__tableWidget.resizeRowsToContents()
        self.__tableWidget.resizeColumnsToContents()
        self.__tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.__tableWidget.horizontalHeader().setSectionsClickable(False)
        self.__tableWidget.horizontalHeader().setStyleSheet("font-weight: bold;")
        self.__tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.__tableWidget.verticalHeader().setSectionsClickable(False)
        self.__tableWidget.verticalHeader().setStyleSheet("font-weight: bold;")

        # Main Layout
        self.__mainLayout.addWidget(self.__classWidget)
        self.__mainLayout.addWidget(self.__nameWidget)
        self.__mainLayout.addWidget(self.__tableWidget)
        self.setLayout(self.__mainLayout)

        # Handler for the buttons
        self.__classToolButton.clicked.connect(lambda: self.__nameWidget.show() or self.__classWidget.hide())
        self.__nameToolButton.clicked.connect(lambda: self.__nameWidget.hide() or self.__classWidget.show())

        # Hide the search-by-name widget
        self.__nameWidget.hide()


class SteelMaterialWidget(QWidget):
    def __init__(self, data = {}) -> None:
        super().__init__()
        self.__data = data

        self.__label = QLabel(self)
        self.__label.setText("UNDER CONSTRUCTION")

        colorEffect = QGraphicsColorizeEffect()
        colorEffect.setColor(Qt.red)
        self.__label.setGraphicsEffect(colorEffect)
