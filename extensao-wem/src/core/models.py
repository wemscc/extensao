from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .widgets import *
from .data import *

from typing import Type

# TODO: Read all data from a binary file / database

class RoofDataModel:
    def __init__(self, *displayWidgets, dataSelector: Type[QComboBox], data = {}) -> None:
        self.__data = data

        # Roof tiles list
        self.__roofTiles = QStringListModel([entry for entry in self.__data])

        # Data related to each tile
        rows = len(data)
        columns = len(list(data)[0])
        self.__roofTileItems = QStandardItemModel(rows, columns)

        # Iterate through all types of tiles and get their respective datas
        for i, entry in enumerate(self.__data):
            for j, value in enumerate(self.__data[entry].values()):
                item = QStandardItem(str(value))
                self.__roofTileItems.setItem(i, j, item)

        # Mapper
        self.__mapper = QDataWidgetMapper()
        self.__mapper.setModel(self.__roofTileItems)

        # Set up the model
        dataSelector.setModel(self.__roofTiles)

        for i, widget in enumerate(displayWidgets):
            self.__mapper.addMapping(widget, i)
        self.__mapper.toFirst()

        # Handler for the selector
        dataSelector.currentIndexChanged.connect(lambda: self.__mapper.setCurrentIndex(dataSelector.currentIndex()))
    

class StateDataModel:
    def __init__(self, dataSelector: Type[QComboBox], displayList: Type[QListWidget], data = {}) -> None:
        self.__data = data
        
        # States list
        self.__states = [State(self.__data[state]) for state in self.__data]

        # Names
        self.__statesNames = QStringListModel([str(name) for name in self.__states])

        # Set up the model
        dataSelector.setModel(self.__statesNames)

        # Add first item to the list
        self.__AddItems(dataSelector, displayList)

        # Handler for the selector
        dataSelector.currentIndexChanged.connect(lambda: self.__AddItems(dataSelector, displayList))

    def __AddItems(self, signalHandler, listWidget):
        self.__attributes = ["Umidade"]

        listWidget.clear()
        for att, value in zip(self.__attributes, self.__states[signalHandler.currentIndex()]()):
            listWidget.addItem("{0}: {1}".format(att, value))

    # def getHumidade(self,signalHandler,estado):
    #  print(f'{estado} estado')


              


class MaterialDataModel:
    def __init__(self, dataSelector: Type[QComboBox], layout: Type[QLayout], data = {}) -> None:
        self.__data = data

        # Create the materials and put them in a list
        self.__materials = [MaterialFactory.CreateMaterial(data) for data in self.__data.values()]

        # List of materials available
        self.__materialsAvailable = QStringListModel([str(name) for name in self.__materials])

        # Set model
        dataSelector.setModel(self.__materialsAvailable)

        # Create a widget associated with the selected material and load it
        self.__material = self.__materials[dataSelector.currentIndex()]   
        widget = MaterialWidgetFactory.CreateWidget(self.__material.Data)
        layout.addWidget(widget)

        # Handler for the selector
        dataSelector.currentIndexChanged.connect(lambda: self.__LoadWidget(dataSelector, layout))
    
    def __LoadWidget(self, signalHandler, layout):
        # Remove the current loaded widget
        currentWidget = layout.itemAt(layout.count() - 1).widget()
        currentWidget.deleteLater()

        # Create a new widget and place it inside the layout
        material  = self.__materials[signalHandler.currentIndex()]
        newWidget = MaterialWidgetFactory.CreateWidget(material.Data)
        layout.addWidget(newWidget)