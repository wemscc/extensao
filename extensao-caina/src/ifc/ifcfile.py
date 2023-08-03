# -*- coding: utf-8 -*-
import ifcopenshell
from ifcopenshell.api import run
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

from .ifcentity import *

@dataclass
class FileData:
    contexts:  defaultdict[dict] = field(default_factory=lambda: defaultdict(dict))
    entities:  defaultdict[dict] = field(default_factory=lambda: defaultdict(dict))
    materials: defaultdict[dict] = field(default_factory=lambda: defaultdict(dict))

class IFCFile:
    def __init__(self):
        # Create a blank IFC file
        self.__instance = ifcopenshell.file(schema='IFC4')

        # Create a container to hold our file data
        self.__data = FileData()


    def GetInstance(self):
        return self.__instance


    def GetContexts(self):
        return self.__data.contexts


    def Write(self, fileName):
        self.__instance.write('./build/' + fileName + ".ifc")


    def AddEntity(self, ent):
        self.__data.entities[ent] = run("root.create_entity", self.__instance, ifc_class=ent.GetIfcClass(), name=ent.GetName())


    def AssignEntity(self, ent, target):
        run("aggregate.assign_object", self.__instance, relating_object=self.__data.entities[target], product=self.__data.entities[ent])


    def AssignContainer(self, ent, container):
        run("spatial.assign_container", self.__instance, relating_structure=self.__data.entities[container], product=self.__data.entities[ent])


    def AddWallRepresentation(self, wall):
        representation = run("geometry.add_wall_representation", self.__instance, context=self.__data.contexts["Body"], length=wall.dimension, height=wall.height, thickness=wall.thickness, x_angle=wall.angle)
        run("geometry.assign_representation", self.__instance, product=self.__data.entities[wall], representation=representation)


    def AddBeamRepresentation(self, beam):
        profile = self.__instance.create_entity("IfcIShapeProfileDef", ProfileType="AREA", OverallWidth=beam.width, OverallDepth=beam.depth, WebThickness=beam.webThickness, FlangeThickness=beam.flangeThickness, FilletRadius=beam.filletRadius)
        representation = run("geometry.add_profile_representation", self.__instance, context=self.__data.contexts["Body"], profile=profile, depth=beam.height)
        run("geometry.assign_representation", self.__instance, product=self.__data.entities[beam], representation=representation)

    def AddProfileRepresentation(self, element, profile):
        
        representation = run("geometry.add_profile_representation", self.__instance, context=self.__data.contexts["Body"], profile=profile, depth=element.height)
        run("geometry.assign_representation", self.__instance, product=self.__data.entities[element], representation=representation)

    #def AddAxisRepresentation(self,element,profile):
     #   axis = ifcopenshell.api.run("geometry.add_axis_representation", self.__instance, context=self.__data.contexts["Body"], axis=[(0.0, 0.0), (1.0, 0.0)])
     
    #def AddIProfileRepresentation(self, element):
     #   profile = self.__instance.create_entity("IfcIShapeProfileDef", ProfileType="AREA", OverallWidth=element.width, OverallDepth=element.depth, WebThickness=element.webThickness, FlangeThickness=element.flangeThickness, FilletRadius=element.filletRadius)
      #  representation = run("geometry.add_profile_representation", self.__instance, context=self.__data.contexts["Body"], profile=profile, depth=element.height)
       # run("geometry.assign_representation", self.__instance, product=self.__data.entities[element], representation=representation)
        

    def EditObjectPlacement(self, obj, transform):
        run("geometry.edit_object_placement", self.__instance, product=self.__data.entities[obj], matrix=transform.GetData())


    def AddMaterial(self, mat, styleClass=None, att=None):
        material = run("material.add_material", self.__instance, name=mat.GetName(), category=mat.GetCategory())

        style = run("style.add_style", self.__instance)
        run("style.add_surface_style", self.__instance, style=style, ifc_class=styleClass, attributes=att)
        run("style.assign_material_style", self.__instance, material=material, style=style, context=self.__data.contexts["Body"])
        
        self.__data.materials[mat.GetName()] = material


    def AssignMaterial(self, obj, mat):
        run("material.assign_material", self.__instance, product=self.__data.entities[obj], material=self.__data.materials[mat])
