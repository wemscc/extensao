# -*- coding: utf-8 -*-
import os
import sys
from ifcopenshell.api import run
from dataclasses import dataclass

from .ifcmaterial import *
from .ifcentity import *
from .ifcfile import *

from math import *

sys.path.append("../definitions")
from definitions import temp
from definitions import constants

sys.path.append("../core")
from core import structural

@dataclass
class StructureSettings:
    width  : float = 10.0
    length : float = 10.0
    floors : int   = 1

    def __init__(self, width=10.0, length=10.0, floors=1):
        width  = width
        length = length
        floors = floors

@dataclass
class RoofSettings:
    pass

@dataclass
class RegionSettings:
    pass

@dataclass
class MaterialSettings:
    material = IFCWoodMat(25,480,13,0.8)      
    
    
class Project:
    def __init__(self,
                 structureSettings = StructureSettings(), 
                 materialSettings = MaterialSettings(), 
                 roofSettings = RoofSettings(), 
                 regionSettings = RegionSettings()):
        
        self.__structure = structureSettings
        self.__material = materialSettings
        self.__roof = roofSettings
        self.__region = regionSettings
  
    def GenerateIFCFile(self, name="untitled"):
        # Create a blank IFC file
        ifcFile = IFCFile()

        # A new IFC project. Setup everything we need before-hand
        # WARNING: an IFCProject MUST be created before anything else!
        project = self.__InitIFCProject(ifcFile)

        # Create a site to place our building. Many hierarchies can be created in a tree-like structure
        site = IFCEntity(ifcFile, "Terreno", ifcClass="IfcSite")

        # Create a building container entity
        building = IFCEntity(ifcFile, "Casa", ifcClass="IfcBuildingStorey")

        # Since the site is our top level location, assign it to the project. Then assign the building to our site
        ifcFile.AssignEntity(site, project)
        ifcFile.AssignEntity(building, site)

        # WALL TEST
        #wall = IFCWall(ifcFile, "Parede", dims=self.structure.length, height=1.0, thickness=0.5, angle=30.0)
        #ifcFile.AssignContainer(wall, building)

        # BUILDING TEST
        # TODO: safe as a prefab, read and load file at run time
        walls = [
            IFCWall(ifcFile, name="Wall0", dims=self.__structure.width , trans=Transform(pos=[0.0, 0.0, 0.0],                           rot=[0.0, 0.0, 00.0])),
            IFCWall(ifcFile, name="Wall1", dims=self.__structure.length, trans=Transform(pos=[self.__structure.width, 0.0, 0.0],        rot=[0.0, 0.0, 90.0])),
            IFCWall(ifcFile, name="Wall2", dims=self.__structure.width , trans=Transform(pos=[0.0, self.__structure.length - 0.2, 0.0], rot=[0.0, 0.0, 00.0])),
            IFCWall(ifcFile, name="Wall3", dims=self.__structure.length, trans=Transform(pos=[0.2, 0.0, 0.0],                           rot=[0.0, 0.0, 90.0]))
        ]
        
        for wall in walls:
            ifcFile.AssignContainer(wall, building)

        pilarQuantity = (1+math.ceil(self.__structure.length/5))
            
        pilares1 = [self.GenerateColumn(ifcFile, self.__material.material, i, 0.1) for i in range(pilarQuantity)]
        pilares2 = [self.GenerateColumn(ifcFile, self.__material.material, i, self.__structure.width-0.1) for i in range(pilarQuantity)]

        for pilar in pilares1:
            ifcFile.AssignContainer(pilar, building)

        for pilar in pilares2:
            ifcFile.AssignContainer(pilar, building)        
            

        tesouras = [self.GenerateRoofScisor(ifcFile, self.__structure.width, self.__material.material, temp.roofInclination, yPos=i*(self.__structure.length/(pilarQuantity-1))) for i in range(pilarQuantity)]

        for tesoura in tesouras:
            for banzoSuperior in tesoura[0]:
                ifcFile.AssignContainer(banzoSuperior, building)
            
            ifcFile.AssignContainer(tesoura[1], building)

            for diagonal in tesoura[2]:
                ifcFile.AssignContainer(diagonal, building)

        
        # Write to file
        ifcFile.Write(name)

    # TODO: Read these settings from a file
    def __InitIFCProject(self, ifcFile):
        project = IFCEntity(ifcFile, "PyCasa", ifcClass="IfcProject")

        # Create a new 3D context for vizualization
        contexts = ifcFile.GetContexts()
        contexts["Model"] = run("context.add_context", ifcFile.GetInstance(), context_type="Model")
        contexts["Body"]  = run("context.add_context", ifcFile.GetInstance(), context_type="Model", context_identifier="Body", target_view="MODEL_VIEW", parent=contexts["Model"])

        # Init materials
        # TODO: parse these from a file

        ifcFile.AddMaterial(IFCDefaultMat(),  styleClass="IfcSurfaceStyleShading", att={ "SurfaceColour" : { "Name" : None, "Red" : 1.0, "Green" : 0.0, "Blue" : 1.0}, "Transparency" : 0.0 })
        ifcFile.AddMaterial(IFCConcreteMat(), styleClass="IfcSurfaceStyleShading", att={ "SurfaceColour" : { "Name" : None, "Red" : .50, "Green" : .50, "Blue" : .50}, "Transparency" : 0.0 })
        ifcFile.AddMaterial(IFCWoodMat(25,480,13,0.8) ,     styleClass="IfcSurfaceStyleShading", att={ "SurfaceColour" : { "Name" : None, "Red" : .50, "Green" : .35, "Blue" : .25}, "Transparency" : 0.0 })

        return project

    def GenerateColumn(self, ifcFile, mat, i, xPos):
        
       if mat.GetCategory()=="wood":
           supportLoad = structural.WoodSupportLoad(self.__structure.width, self.__structure.length, temp.weightRoofTiles, temp.roofInclination, temp.montantes, mat)

           profile = ifcFile.GetInstance().create_entity("IfcRectangleProfileDef", ProfileType="AREA", XDim= structural.GetXDimention(supportLoad,mat), YDim=structural.GetYDimention(supportLoad,mat))

           #profile = RectangleProfile(width = structural.GetXDimention(supportLoad,mat), depth = structural.GetYDimention(supportLoad,mat))

           pilarYDistancing = 5

           return IFCColumn(ifcFile, profile = profile, trans=Transform(pos=[xPos, pilarYDistancing*i, 0.0],rot=[0.0, 0.0, 0.0]) )

    def KnotCoordenates(self, i, espacamentoTerca, nBottomChords, nTopChords, width, roofExtention, roofInclination, nKnots, evenCheck):
        i += 1

        topChord = espacamentoTerca
        firstTopChord = roofExtention - (nTopChords-1)*topChord
        
        firstBottomChord = roofExtention - nTopChords*espacamentoTerca + (width - 2*math.cos(roofInclination)*(roofExtention - nTopChords*espacamentoTerca))/(nBottomChords+1)
        bottomChord = (width - 2*math.cos(roofInclination)*(roofExtention - nTopChords*espacamentoTerca))/(nBottomChords+1)

        x = 0.0
        z = 0.0
                             
        if evenCheck == True:
            
            if i == 1:
                x = 0.0
                z = 0.0

            if i%2 == 0:
                x = math.cos(roofInclination)*(firstTopChord+(((i/2)-1)*topChord))
                z = math.sin(roofInclination)*(firstTopChord+(((i/2)-1)*topChord))

                if i > math.floor(nKnots/2):
                    tempI = nKnots + 1 - i

                    x = width - (math.cos(roofInclination)*(firstTopChord+(((tempI/2)-1)*topChord)))
                    z = math.sin(roofInclination)*(firstTopChord+(((tempI/2)-1)*topChord))             
                    
            if i%4 == 1 and i!=1:
                x = firstBottomChord + bottomChord + ((i-5)/4)*bottomChord
                z = 0.0

                if i > math.ceil(nKnots/2):
                    tempI = nKnots + 1 - i

                    x = width - (math.cos(roofInclination)*(firstTopChord+topChord)+((tempI-7)/4)*(math.cos(roofInclination)*(2*topChord))+bottomChord)
                    z = math.sin(roofInclination)*(firstTopChord+topChord)+((tempI-7)/4)*(math.sin(roofInclination)*(2*topChord))

            if i%4 == 3 and i!=nKnots:
                x = math.cos(roofInclination)*(firstTopChord+topChord)+((i-7)/4)*(math.cos(roofInclination)*(2*topChord))+bottomChord
                z = math.sin(roofInclination)*(firstTopChord+topChord)+((i-7)/4)*(math.sin(roofInclination)*(2*topChord))

                if i==3:
                    z = 0.0

                if i > math.ceil(nKnots/2):
                    tempI = nKnots + 1 - i

                    x = width - (firstBottomChord + bottomChord + ((tempI-5)/4)*bottomChord)
                    z = 0.0
                                         
            if i == nKnots:
                x = width
                z = 0.0

        if evenCheck == False:

            if i == 1:
                x = 0.0
                z = 0.0

            if i%2 == 0:
                x = math.cos(roofInclination)*(firstTopChord+(((i/2)-1)*topChord))
                z = math.sin(roofInclination)*(firstTopChord+(((i/2)-1)*topChord))

                if i > math.floor(nKnots/2):
                    tempI = nKnots + 1 - i

                    x = width - (math.cos(roofInclination)*(firstTopChord+(((tempI/2)-1)*topChord)))
                    z = math.sin(roofInclination)*(firstTopChord+(((tempI/2)-1)*topChord))

            if i%4 == 1 and i != 1:
                hipotenusaDireita=((math.sin(roofInclination)*(firstTopChord+(topChord*((i-5)/4)*2)))*math.sqrt((math.sin(roofInclination)*(firstTopChord+((math.floor(i/4)*2)*topChord)))**2+(math.cos(roofInclination)*(firstTopChord+((math.floor(i/4)*2)*topChord))-(firstBottomChord+((((i-5)/4))*bottomChord)))**2))/(math.sin(roofInclination)*(firstTopChord+((math.floor(i/4)*2)*topChord)))
                catetoDireito=math.sqrt((hipotenusaDireita**2)-(math.sin(roofInclination)*(firstTopChord+(topChord*((i-5)/4)*2)))**2)


                x = math.cos(roofInclination)*(firstTopChord+(topChord*((i-5)/4)*2)) + firstBottomChord+(bottomChord*((i-5)/4))-(math.cos(roofInclination)*(firstTopChord+(topChord*((i-5)/4)*2)))+catetoDireito
                z = math.sin(roofInclination)*firstTopChord+((i-5)/4)*(math.sin(roofInclination)*(2*topChord))

                if i > math.ceil(nKnots/2):
                    tempI = nKnots + 1 - i
                    
                    x = width - (firstBottomChord + (math.floor(tempI/4)*bottomChord))
                    z = 0.0

            if i%4 == 3 and i != nKnots:
                x = firstBottomChord + math.floor(i/4)*bottomChord
                z = 0.0

                if i > math.ceil(nKnots/2):
                    tempI = nKnots + 1 - i

                    hipotenusaDireita=((math.sin(roofInclination)*(firstTopChord+(topChord*((tempI-5)/4)*2)))*math.sqrt((math.sin(roofInclination)*(firstTopChord+((math.floor(tempI/4)*2)*topChord)))**2+(math.cos(roofInclination)*(firstTopChord+((math.floor(tempI/4)*2)*topChord))-(firstBottomChord+((((tempI-5)/4))*bottomChord)))**2))/(math.sin(roofInclination)*(firstTopChord+((math.floor(tempI/4)*2)*topChord)))
                    catetoDireito=math.sqrt((hipotenusaDireita**2)-(math.sin(roofInclination)*(firstTopChord+(topChord*((tempI-5)/4)*2)))**2)
                    
                    x = width - (math.cos(roofInclination)*(firstTopChord+(topChord*((tempI-5)/4)*2)) + firstBottomChord+(bottomChord*((tempI-5)/4))-(math.cos(roofInclination)*(firstTopChord+(topChord*((tempI-5)/4)*2)))+catetoDireito)
                    z = math.sin(roofInclination)*firstTopChord+((tempI-5)/4)*(math.sin(roofInclination)*(2*topChord))

            if i == nKnots:
                x = width
                z = 0.0

        
        return [x,z]

    def ElementsConectivity(self, i, nKnots, nElements, nChords, evenCheck):
        
        i += 1
        nKnots -= 1

        firstKnot = 0
        secondKnot = 0

        if evenCheck == True:

            #primeiros cinco elementos
            if i == 1:
                firstKnot = 0
                secondKnot = 1

            if i >= 2 and i <= 5:
                firstKnot = i - 2
                secondKnot = i

            #elementos inferiores
            if (i-7)%3 == 0 and i>5 and i<=nChords-5:
                firstKnot = 4 + 4*((i-7)/3)
                if i > math.ceil(nChords/2):
                    firstKnot += 2;

                secondKnot = firstKnot + 4
                
                if i == math.ceil(nChords/2):
                    secondKnot += 2

            #elementos superiores
            if (i-6)%3 == 0 and i>5 and i<=nChords-5:
                firstKnot = 5 + 4*((i-6)/3)
                secondKnot = firstKnot + 2

            if (i-8)%3 == 0 and i>5 and i<=nChords-5:
                firstKnot = 7 + 4*((i-8)/3)
                secondKnot = firstKnot + 2

            #últimos cinco elementos inferiores e superiores
            if i <= nChords-1 and i > nChords-5:
                tempI= nChords - i

                firstKnot = nKnots - (tempI + 1)
                secondKnot = nKnots - (tempI - 1)

            if i == nChords:
                firstKnot = nKnots - 1
                secondKnot = nKnots

            #diagonais
            if (i-nChords)%5 == 1 and i>nChords:
                firstKnot = 1 + 4*((i-nChords-1)/5)
                secondKnot = firstKnot+1

                if i > math.ceil((nElements - nChords)/2)+nChords:
                    tempI = nElements + 1 - i

                    secondKnot = nKnots - (3 + 4*((tempI-4)/5))
                    firstKnot = secondKnot - 3
                
            if (i-nChords)%5 == 2 and i>nChords:
                firstKnot = 2 + 4*((i-nChords-2)/5)
                secondKnot = firstKnot+1

                if i > math.ceil((nElements - nChords)/2)+nChords:
                    tempI = nElements + 1 - i

                    firstKnot = nKnots - (4 + 4*((tempI-3)/5))
                    secondKnot = firstKnot + 1

            if (i-nChords)%5 == 3 and i>nChords:
                firstKnot = 3 + 4*((i-nChords-3)/5)
                secondKnot = firstKnot+1

                if i > math.ceil((nElements - nChords)/2)+nChords:
                    tempI = nElements + 1 - i

                    secondKnot = nKnots - (2 + 4*((tempI-2)/5))
                    firstKnot = secondKnot - 1
                    
            if (i-nChords)%5 == 4 and i>nChords:
                firstKnot = 3 + 4*((i-nChords-4)/5)
                secondKnot = firstKnot+3

                if i > math.ceil((nElements - nChords)/2)+nChords:
                    tempI = nElements + 1 - i

                    firstKnot = nKnots - (2 + 4*((tempI-1)/5))
                    secondKnot = firstKnot+1
                    
            if (i-nChords)%5 == 0 and i>nChords:
                firstKnot = 4 + 4*((i-nChords-5)/5)
                secondKnot = firstKnot+2

                if i > math.ceil((nElements - nChords)/2)+nChords:
                    tempI = nElements + 1 - i

                    secondKnot = nKnots - (4 + 4*((tempI-5)/5))
                    firstKnot = secondKnot - 2

        if evenCheck == False:

            #primeiros três elementos
            if i == 1:
                firstKnot = 0
                secondKnot = 1

            if i == 2 or i == 3:
                firstKnot = i - 2
                secondKnot = i

            #elementos inferiores
            if (i-5)%3 == 0 and i>3 and i<=nChords-3:
                firstKnot = 2 + 4*((i-5)/3)
                if i > math.ceil(nChords/2):
                    firstKnot += 2;

                secondKnot = firstKnot + 4
                
                if i == math.ceil(nChords/2):
                    secondKnot += 2

            #elementos superiores
            if (i-4)%3 == 0 and i>3 and i<=nChords-3:
                firstKnot = 3 + 4*((i-4)/3)
                secondKnot = firstKnot + 2

            if (i-6)%3 == 0 and i>3 and i<=nChords-3:
                firstKnot = 5 + 4*((i-6)/3)
                secondKnot = firstKnot + 2

            #últimos três elementos inferiores e superiores
            if i == nChords-1 or i == nChords-2:
                tempI= nChords - i

                firstKnot = nKnots - (tempI + 1)
                secondKnot = nKnots - (tempI - 1)

            if i == nChords:
                firstKnot = nKnots - 1
                secondKnot = nKnots     

            #diagonais
            if (i-nChords)%5 == 1 and i>nChords:
                firstKnot = 1 + 4*((i-nChords-1)/5)
                secondKnot = firstKnot+1

                if i > math.ceil((nElements - nChords)/2)+nChords:
                    tempI = nElements + 1 - i

                    firstKnot = nKnots - (5 + 4*((tempI-5)/5))
                    secondKnot = firstKnot + 1

            if (i-nChords)%5 == 2 and i>nChords:
                firstKnot = 1 + 4*((i-nChords-2)/5)
                secondKnot = firstKnot+3

                if i > math.ceil((nElements - nChords)/2)+nChords:
                    tempI = nElements + 1 - i

                    firstKnot = nKnots - (4 + 4*((tempI-4)/5))
                    secondKnot = firstKnot+1

            if (i-nChords)%5 == 3 and i>nChords:
                firstKnot = 2 + 4*((i-nChords-3)/5)
                secondKnot = firstKnot+2

                if i > math.ceil((nElements - nChords)/2)+nChords:
                    tempI = nElements + 1 - i

                    firstKnot = nKnots - (4 + 4*((tempI-3)/5))
                    secondKnot = firstKnot+2

            if (i-nChords)%5 == 4 and i>nChords:
                firstKnot = 3 + 4*((i-nChords-4)/5)
                secondKnot = firstKnot+1

                if i > math.ceil((nElements - nChords)/2)+nChords:
                    tempI = nElements + 1 - i

                    firstKnot = nKnots - (4 + 4*((tempI-2)/5))
                    secondKnot = firstKnot+3

            if (i-nChords)%5 == 0 and i>nChords:
                firstKnot = 4 + 4*((i-nChords-5)/5)
                secondKnot = firstKnot+1

                if i > math.ceil((nElements - nChords)/2)+nChords:
                    tempI = nElements + 1 - i

                    firstKnot = nKnots - (2 + 4*((tempI-1)/5))
                    secondKnot = firstKnot+1
           
        return [int(firstKnot), int(secondKnot)]
    
    #usei Chord, mas a traducao correta e rafter
    def GenerateTopChords(self, ifcFile, mat, i, yPos, roofExtention, roofInclination, width):
 
        if mat.GetCategory()=="wood":
                    
                              
            profile = ifcFile.GetInstance().create_entity("IfcRectangleProfileDef", ProfileType="AREA", XDim=0.12, YDim=0.06)
            
            length = roofExtention

           
            if i == 0:
                xPos = 0.0
                rotation = 90 - degrees(roofInclination)
            else:
                xPos = width
                rotation = 270 + degrees(roofInclination)
                              
            return IFCMember(ifcFile, profile = profile, name="Member", height=length, mat="Default", trans=Transform(pos=[xPos, yPos, 4.0],rot=[0.0, rotation , 0.0]))

    #usei Chord, mas a traducao correta e rafter
    def GenerateBottomChord(self, ifcFile, mat, yPos, width):

        trussHight = 4

        if mat.GetCategory()=="wood":
                                 
            profile = ifcFile.GetInstance().create_entity("IfcRectangleProfileDef", ProfileType="AREA", XDim=0.12, YDim=0.06) 
            
        return IFCMember(ifcFile, profile = profile, name="Member", height=width, mat="Default", trans=Transform(pos=[0.0, yPos, trussHight],rot=[0.0, 90 , 0.0]))

    def GenerateStrut(self, ifcFile, mat, i, yPos, knots, nStruts, conectivity, nChords, evenCheck):

        trussHight = 4
        strutId = i + 1
        matrixId = i + nChords

        xFirstKnot = knots[conectivity[matrixId][0]][0]
        zfirstKnot = knots[conectivity[matrixId][0]][1]

        xSecondKnot = knots[conectivity[matrixId][1]][0]
        zSecondKnot = knots[conectivity[matrixId][1]][1]

        if mat.GetCategory() == "wood":
            profile = ifcFile.GetInstance().create_entity("IfcRectangleProfileDef", ProfileType="AREA", XDim=0.12, YDim=0.06)

        if evenCheck == True:

            if strutId%5 == 1 and strutId <= nStruts/2 or strutId%5 == 3 and strutId <= nStruts/2:
                length = math.sqrt((zfirstKnot-zSecondKnot)**2+(xSecondKnot-xFirstKnot)**2)
                xPos = xSecondKnot
                zPos = zSecondKnot
                rotation = 270 + degrees(math.atan((zfirstKnot-zSecondKnot)/(xSecondKnot-xFirstKnot)))

            if strutId%5 == 2 and strutId <= nStruts/2 or strutId%5 == 0 and strutId <= nStruts/2:
                length = math.sqrt((zSecondKnot-zfirstKnot)**2+(xSecondKnot-xFirstKnot)**2)
                xPos = xFirstKnot
                zPos = zfirstKnot
                rotation = 90 - degrees(math.atan((zSecondKnot-zfirstKnot)/(xSecondKnot-xFirstKnot)))

            if strutId%5 == 4 and strutId <= nStruts/2:
                length = xSecondKnot - xFirstKnot
                xPos = xFirstKnot
                zPos = zfirstKnot
                rotation = 90

            if strutId%5 == 1 and strutId > nStruts/2:
                length = xSecondKnot - xFirstKnot
                xPos = xFirstKnot
                zPos = zfirstKnot
                rotation = 90
        
            if strutId%5 == 2 and strutId > nStruts/2 or strutId%5 == 4 and strutId > nStruts/2:
                length = math.sqrt((zSecondKnot-zfirstKnot)**2+(xSecondKnot-xFirstKnot)**2)
                xPos = xFirstKnot
                zPos = zfirstKnot
                rotation = 90 - degrees(math.atan((zSecondKnot-zfirstKnot)/(xSecondKnot-xFirstKnot)))

            if strutId%5 == 3 and strutId > nStruts/2 or strutId%5 == 0 and strutId > nStruts/2:
                length = math.sqrt((zfirstKnot-zSecondKnot)**2+(xSecondKnot-xFirstKnot)**2)
                xPos = xSecondKnot
                zPos = zSecondKnot
                rotation = 270 + degrees(math.atan((zfirstKnot-zSecondKnot)/(xSecondKnot-xFirstKnot)))

        if evenCheck == False:

            if strutId%5 == 1 and strutId <= nStruts/2 or strutId%5 == 4 and strutId <= nStruts/2:
                length = math.sqrt((zfirstKnot-zSecondKnot)**2+(xSecondKnot-xFirstKnot)**2)
                xPos = xSecondKnot
                zPos = zSecondKnot
                rotation = 270 + degrees(math.atan((zfirstKnot-zSecondKnot)/(xSecondKnot-xFirstKnot)))

            if strutId%5 == 2 and strutId <= nStruts/2:
                length = xSecondKnot - xFirstKnot
                xPos = xFirstKnot
                zPos = zfirstKnot
                rotation = 90

            if strutId%5 == 3 and strutId <= nStruts/2 or strutId%5 == 0 and strutId <= nStruts/2:
                length = math.sqrt((zSecondKnot-zfirstKnot)**2+(xSecondKnot-xFirstKnot)**2)
                xPos = xFirstKnot
                zPos = zfirstKnot
                rotation = 90 - degrees(math.atan((zSecondKnot-zfirstKnot)/(xSecondKnot-xFirstKnot)))

            if strutId%5 == 1 and strutId > nStruts/2 or strutId%5 == 3 and strutId > nStruts/2:
                length = math.sqrt((zfirstKnot-zSecondKnot)**2+(xSecondKnot-xFirstKnot)**2)
                xPos = xSecondKnot
                zPos = zSecondKnot
                rotation = 270 + degrees(math.atan((zfirstKnot-zSecondKnot)/(xSecondKnot-xFirstKnot)))

            if strutId%5 == 2 and strutId > nStruts/2 or strutId%5 == 0 and strutId > nStruts/2:
                length = math.sqrt((zSecondKnot-zfirstKnot)**2+(xSecondKnot-xFirstKnot)**2)
                xPos = xFirstKnot
                zPos = zfirstKnot
                rotation = 90 - degrees(math.atan((zSecondKnot-zfirstKnot)/(xSecondKnot-xFirstKnot)))

            if strutId%5 == 4 and strutId > nStruts/2:
                length = xSecondKnot - xFirstKnot
                xPos = xFirstKnot
                zPos = zfirstKnot
                rotation = 90

        return IFCMember(ifcFile, profile = profile, name = "Member", height=length, mat="Default", trans=Transform(pos=[xPos, yPos, trussHight + zPos],rot=[0.0, rotation , 0.0]))

    def GenerateRoofScisor(self, ifcFile, width, mat, inclination, yPos):

        roofInclination = math.atan(inclination/100)
        
        roofExtention = (width/2)/math.cos(roofInclination)

        nTopChords = math.floor(roofExtention/constants.espacamentoMinimoTerca)
            
        #decide o espacamento das tercas a partir do tamanho da perna da tesoura

        #todos os banzos superiores sao iguais e tem tamanho entre 1,3 e 1,65 m
        if roofExtention%constants.espacamentoMinimoTerca<=nTopChords*(constants.espacamentoMaximoTerca-constants.espacamentoMinimoTerca):
            espacamentoTerca=roofExtention/nTopChords
        #Os banzos superiores sao iguais e tem tamanho de 1,65 m, com excess�o ao �ltimo que � maior
        elif roofExtention<=(nTopChords*constants.espacamentoMaximoTerca)+constants.MaximoEspacamentoEspecial:
            espacamentoTerca=constants.espacamentoMaximoTerca
            #espacamentoEspecial=roofExtention-espacamentoTerca*(nTopChords-1)
        #Os banzos superiores sao iguais e tem tamanho de 1,30 m, com excess�o ao �ltimo que � menor
        elif roofExtention%constants.espacamentoMinimoTerca>nTopChords*(constants.espacamentoMaximoTerca-constants.espacamentoMinimoTerca) and roofExtention>(nTopChords*constants.espacamentoMaximoTerca)+constants.MaximoEspacamentoEspecial:
            nTopChords+=1
            espacamentoTerca=constants.espacamentoMinimoTerca
            #espacamentoEspecial=roofExtention%constants.espacamentoMinimoTerca
                    
        #quantidade de banzos inferiores
        nBottomChords=(math.floor(nTopChords/2))*2+1

        nChords = nBottomChords + 2*nTopChords

        #Se o numero de banzos superiores por �gua for par ou impar
        if nTopChords%2==0:
            nStruts=int((2+((nTopChords-2)/2)*5)*2)
            evenCheck = True
        else:
            nStruts=int(math.floor(nTopChords/2)*10)
            evenCheck = False

        nKnots = nTopChords*4 - 1

        nElements = nKnots*2 - 3
                
        nos = [self.KnotCoordenates(i, espacamentoTerca, nBottomChords, nTopChords, width, roofExtention, roofInclination, nKnots, evenCheck) for i in range(nKnots)]

        elementos = [self.ElementsConectivity(i, nKnots, nElements, nChords, evenCheck) for i in range(nElements)]
                
        banzosSuperiores = [self.GenerateTopChords(ifcFile, mat, i, yPos, roofExtention, roofInclination, width) for i in range(2)]
        
        banzoInferior = self.GenerateBottomChord(ifcFile, mat, yPos, width)
        
        diagonais = [self.GenerateStrut(ifcFile, mat, i, yPos, nos,  nStruts, elementos, nChords, evenCheck) for i in range(nStruts)]
        
        return [banzosSuperiores, banzoInferior, diagonais]


