# -*- coding: utf-8 -*-
from ifcopenshell.api import run
from enum import Enum
from abc import ABC, abstractmethod
import math
import sys

sys.path.append("../definitions")
from definitions import constants

class Material(ABC):
    def __init__(self, name, category):
        self._name = name
        self._category = category

    def GetName(self):
        return self._name

    def GetCategory(self):
        return self._category

    def GetMaterialWeight(self):
        return self._especificWeight

    

    def GetXDimention(self):
        return 0.3

    def GetYDimention(self):
        return 0.15

class Default(Material):
    def __init__(self):
        super().__init__(name="Default", category=None)

class Concrete(Material):
    def __init__(self):
        super().__init__(name="Concreto", category="concrete")

class Wood(Material):
    def __init__(self, resistanceParallelCompression, caracteristicElasticity, averageDensity, relativeHumidity):
        super().__init__(name="Madeira", category="wood")
        self._Fck=resistanceParallelCompression*1000 #convert Mpa to kN/m²
        self._Ecm=caracteristicElasticity*1000000 #convert Gpa to kN/m²
        self._especificWeight = averageDensity*constants.gravity
        self._relativeHumidity = relativeHumidity
        
    def GetFck(self):
        return self._Fck

    def GetEcm(self):
        return self._Ecm

    def GetRelativeHumidity(self):
        return self._relativeHumidity
    

   
        

