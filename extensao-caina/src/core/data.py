from abc import ABCMeta
from enum import Enum
from .widgets import *

class State:
    def __init__(self, info) -> None:
        self.__info = info
        
    def __str__(self):
        return "{0} ({1})".format(self.__info.get("name"), self.__info.get("acronym"))
          
    def __call__(self):
        return self.__info.get("data").values()


class MaterialFactory:
    MaterialType = Enum('Materials', 'Wood Steel')

    @staticmethod
    def CreateMaterial(data):
        materialType = MaterialFactory.MaterialType[data.get("type")]

        match(materialType):
            case MaterialFactory.MaterialType.Wood:
                return WoodMaterial(data)
            case MaterialFactory.MaterialType.Steel:
                return SteelMaterial(data)
            case _:
                print("Material Factory - Invalid type of material passed. Cannot create material object.")


class IMaterial(metaclass = ABCMeta):
    def __init__(self, data) -> None:
        self._data = data
        
        # Public accessor
        self.Data = self._data

    def __str__(self):
        return "{0}".format(self._data.get("name"))        


class WoodMaterial(IMaterial):
    def __init__(self, data) -> None:
        super().__init__(data)


class SteelMaterial(IMaterial):
    def __init__(self, data) -> None:
        super().__init__(data)