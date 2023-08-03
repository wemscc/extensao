#from typing import Self
import ifcopenshell
import ifcopenshell.geom
import numpy as np
import math

from abc import ABC, abstractmethod
from ifcopenshell.api import run
from enum import Enum
from .ifcmaterial import *
from .linalg import *
from .ifcfile import *

# ===== Entities =====
class IFCEntity:
    def __init__(self, ifcFile=None, name=None, ifcClass=None):
        self._name = name
        self._ifcClass = ifcClass

        # Create this entity in our file
        ifcFile.AddEntity(self)

    def GetName(self):
        return self._name
    
    def GetIfcClass(self):
        return self._ifcClass

# ===== Objects =====
class IFCObject(IFCEntity, ABC):
    def __init__(self, ifcFile=None, name=None, ifcClass=None, transform=None, material=None):
        super().__init__(ifcFile, name, ifcClass)
        self._transform = transform
        self._material = material

        # Place the object in the scene using its transform
        ifcFile.EditObjectPlacement(self, self._transform)

    def GetTransform(self):
        return self._transform

    def SetTransform(self, transform):
        self._transform = transform

    def GetMaterial(self):
        return self._material
    
    def SetMaterial(self, material):
        self._material = material


class IFCWall(IFCObject):
    def __init__(self, ifcFile, name="Wall", dims=5.0, height=4.0, thickness=0.2, angle=0.0, trans=Transform(), mat="Default"):
        super().__init__(ifcFile, name, ifcClass="IfcWall", transform=trans, material=mat)
        self.dimension = dims
        self.height = height
        self.thickness = thickness
        self.angle = np.radians(angle)
        
        ifcFile.AddWallRepresentation(self)
        ifcFile.AssignMaterial(self, mat)


class IFCBeam(IFCObject):
    def __init__(self, ifcFile, name="Beam", height=4.0, width=0.15, depth=0.30, webThickness=0.05, flangeThickness=0.080, filletRadius=0.10, trans=Transform(), mat="Default"):
        super().__init__(ifcFile, name, ifcClass="IfcBeam", transform=trans, material=mat)
        self.height = height
        self.width = width
        self.depth = depth
        self.webThickness = webThickness
        self.flangeThickness = flangeThickness
        self.filletRadius = filletRadius

        ifcFile.AddBeamRepresentation(self)
        ifcFile.AssignMaterial(self, mat)

class IFCColumn(IFCObject):
    def __init__(self, ifcFile, profile, name="Column", height=4.0, mat="Default", trans=Transform() ):
        super().__init__(ifcFile, name, ifcClass="IfcColumn", transform=trans, material=mat)

        self.height = height
        

        '''

        if mat=="steel":
            self.width = profile.X
            self.depth = profile.Y
            self.webThickness = profile.webThickness
            self.flangeThickness = profile.flangeThickness
            self.filletRadius = profile.filletRadius

        '''
        
        ifcFile.AddProfileRepresentation(self, profile)
        ifcFile.AssignMaterial(self, mat)


        


class IFCSlab(IFCObject):
    pass


class IFCMember(IFCObject):
    def __init__(self, ifcFile, profile, name="Member", height=4.0, mat="Default", trans=Transform() ):        
        super().__init__(ifcFile, name, ifcClass="IfcMember", transform=trans, material=mat)

        self.height = height
        
               
        ifcFile.AddProfileRepresentation(self, profile)
        ifcFile.AssignMaterial(self, mat)
