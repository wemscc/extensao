# -*- coding: utf-8 -*-
from ifcopenshell.api import run
from enum import Enum
from abc import ABC, abstractmethod
import math
import sys

sys.path.append("../definitions")
from definitions import constants

class IFCMaterial(ABC):
    def __init__(self, name, category):
        self._name = name
        self._category = category

    def GetName(self):
        return self._name

    def GetCategory(self):
        return self._category

    def GetMaterialWeight(self):
        return self._especificWeight
    
class IFCDefaultMat(IFCMaterial):
    def __init__(self):
        super().__init__(name="Default", category=None)

class IFCConcreteMat(IFCMaterial):
    def __init__(self):
        super().__init__(name="Concreto", category="concrete")

class IFCWoodMat(IFCMaterial):
    def __init__(self, resistanceParallelCompression = 25, caracteristicElasticity = 13, averageDensity = 480000, relativeHumidity = 0.9):
        super().__init__(name="Madeira", category="wood")
        self._Fck=resistanceParallelCompression*1000 #convert Mpa to kN/m2
        self._Ecm=caracteristicElasticity*1000000 #convert Gpa to kN/m2
        self._especificWeight = averageDensity/100 #convert kg/m3 to kN/m3
        self._relativeHumidity = relativeHumidity
        
    def GetFck(self):
        return self._Fck

    def GetEcm(self):
        return self._Ecm

    def GetRelativeHumidity(self):
        return self._relativeHumidity
    
    def setResistanceParallelCompression(self,resistanceParallelCompression):
        self._Fck = resistanceParallelCompression *1000
    
    def setcaracteristicElasticity(self,caracteristicElasticity):
        self._Ecm = caracteristicElasticity *1000000

    def setaverageDensity(self,averageDensity):
        self._especificWeight = averageDensity/100
        
    

   
        

