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
from core import structural, auxiliar 
@dataclass
class StructureSettings:
    width  : float = 10.0
    length : float = 10.0
    floors : int   = 1

@dataclass
class RoofSettings:
    pass

@dataclass
class RegionSettings:
    relativeHumidity : float = 0.5

@dataclass
class MaterialSettings:
    resistanceParallelCompression : int = 25
    caracteristicElasticity : int = 13
    averageDensity : int = 480 
    relativeHumidity : float = 0.9
    material : IFCWoodMat = (resistanceParallelCompression,caracteristicElasticity,averageDensity,relativeHumidity)
    def __post_init__(self):
        self.material = IFCWoodMat(self.resistanceParallelCompression,self.caracteristicElasticity,self.averageDensity,self.relativeHumidity)
       
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

        porticQuantity = (1+math.ceil(self.__structure.length/5))

        porticDistancing = self.__structure.length/(porticQuantity-1)
            
        pilares1 = [self.GenerateColumn(ifcFile, self.__material.material, 0.1, i*porticDistancing) for i in range(porticQuantity)]
        pilares2 = [self.GenerateColumn(ifcFile, self.__material.material, self.__structure.width-0.1, i*porticDistancing) for i in range(porticQuantity)]

        for pilar in pilares1:
            ifcFile.AssignContainer(pilar, building)

        for pilar in pilares2:
            ifcFile.AssignContainer(pilar, building) 


        finkTruss = FinkTruss(ifcFile, self.__material.material, self.__structure.width, porticDistancing, temp.roofInclination)

        tesouras = [finkTruss.GenerateRoofScisor(yPos = i*porticDistancing) for i in range(porticQuantity)]

        for tesoura in tesouras:
            for banzoSuperior in tesoura[0]:
                ifcFile.AssignContainer(banzoSuperior, building)
            
            ifcFile.AssignContainer(tesoura[1], building)

            for diagonal in tesoura[2]:
                ifcFile.AssignContainer(diagonal, building)
                
        
        nTercas = finkTruss.GetTopChords()*2 + 1

        tercas = [self.GenerateTerca(ifcFile, self.__material.material, i, self.__structure.width, self.__structure.length, finkTruss.GetRoofExtention(), finkTruss.GetRoofInclination(), finkTruss.GetEspacamentoTerca(), finkTruss.GetTopChords(), nTercas, tesouras[0][0][0]) for i in range(nTercas)]

        for terca in tercas:
            ifcFile.AssignContainer(terca, building)

        nCaibros = (floor(self.__structure.length/constants.espacamentoCaibro)+1)*2

        caibros = [self.GenerateCaibro(ifcFile, self.__material.material, i, self.__structure.width, self.__structure.length, nCaibros, tesouras[0][0][0], tercas[0], finkTruss.GetRoofExtention(), finkTruss.GetRoofInclination()) for i in range(nCaibros)]

        for caibro in caibros:
            ifcFile.AssignContainer(caibro, building)

        nRipas = (floor(finkTruss.GetRoofExtention()/constants.espacamentoRipa)-3)*2

        #print(nRipas)

        ripas = [self.GenerateRipa(ifcFile, self.__material.material, i, self.__structure.width, self.__structure.length, nRipas, tesouras[0][0][0], tercas[0], caibros[0], finkTruss.GetRoofExtention(), finkTruss.GetRoofInclination()) for i in range(nRipas)]

        for ripa in ripas:
            ifcFile.AssignContainer(ripa, building)

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
        ifcFile.AddMaterial(IFCWoodMat(),     styleClass="IfcSurfaceStyleShading", att={ "SurfaceColour" : { "Name" : None, "Red" : .50, "Green" : .35, "Blue" : .25}, "Transparency" : 0.0 })

        return project

    def GenerateColumn(self, ifcFile, mat, xPos, yPos):
        
       if mat.GetCategory()=="wood":

           supportLoad = structural.WoodPilarSupportLoad(self.__structure.width/2, self.__structure.length, temp.weightRoofTiles, temp.roofInclination, temp.montantes, mat)

           profile = ifcFile.GetInstance().create_entity("IfcRectangleProfileDef", ProfileType="AREA", XDim= structural.GetXDimention(supportLoad,mat), YDim=structural.GetYDimention(supportLoad,mat))

           #profile = RectangleProfile(width = structural.GetXDimention(supportLoad,mat), depth = structural.GetYDimention(supportLoad,mat))

           return IFCColumn(ifcFile, profile = profile, trans=Transform(pos=[xPos, yPos, 0.0],rot=[0.0, 0.0, 0.0]) )
        
    def GenerateTerca(self, ifcFile, mat, i, width, length, roofExtention, roofInclination, espacamentoTerca, nTopChords, nTercas, rafter):

        trussHight = 4.0

        length += rafter.profile.YDim

        yPos = - rafter.profile.YDim/2

        if mat.GetCategory() == "wood":
            profile = ifcFile.GetInstance().create_entity("IfcRectangleProfileDef", ProfileType="AREA", XDim=0.06, YDim=0.12)

        firstTopChord = roofExtention - (nTopChords-1)*espacamentoTerca

        if i < math.floor(nTercas/2):
            xPos = math.cos(roofInclination)*(firstTopChord + ((i-1)*espacamentoTerca))
            zPos = math.cos(roofInclination)*(rafter.profile.XDim/2 + profile.YDim/2) + math.sin(roofInclination)*(profile.XDim/2 + firstTopChord + ((i-1)*espacamentoTerca))
            rotation = - degrees(roofInclination)

            if i == 0:
                xPos = 0
                zPos = math.cos(roofInclination)*(rafter.profile.XDim/2 + profile.YDim/2) + math.sin(roofInclination)*(profile.XDim/2)
                
        elif i >= math.ceil(nTercas/2):
            tempI = nTercas - (i+1)

            xPos = width - (math.cos(roofInclination)*firstTopChord + math.cos(roofInclination)*((tempI-1)*espacamentoTerca))
            zPos = math.cos(roofInclination)*(rafter.profile.XDim/2 + profile.YDim/2) + math.sin(roofInclination)*(profile.XDim/2 + firstTopChord + ((tempI-1)*espacamentoTerca))
            rotation = degrees(roofInclination)

            if i == nTercas - 1:
                xPos = width
                zPos = math.cos(roofInclination)*(rafter.profile.XDim/2 + profile.YDim/2) + math.sin(roofInclination)*(profile.XDim/2) 
                
        else:
            xPos = math.cos(roofInclination)*(firstTopChord + ((i-1)*espacamentoTerca))
            zPos = math.cos(roofInclination)*(rafter.profile.XDim/2) + math.sin(roofInclination)*(firstTopChord + ((i-1)*espacamentoTerca)) + profile.YDim/2 #math.cos(roofInclination)*(rafter.profile.YDim/2) + math.sin(roofInclination)*(firstTopChord + ((i-1)*espacamentoTerca)) + profile.YDim/2
            rotation = 0.0


        return IFCMember(ifcFile, profile = profile, name="Terca" , height=length, mat="Default", trans=Transform(pos=[xPos , yPos, trussHight + zPos],rot=[270.0, rotation, 0.0]))

    def GenerateCaibro(self, ifcFile, mat, i, width, length, nCaibros, rafter, terca, roofExtention, roofInclination):
        if mat.GetCategory() == "wood":
            profile = ifcFile.GetInstance().create_entity("IfcRectangleProfileDef", ProfileType="AREA", XDim=constants.xCaibro, YDim=constants.yCaibro)

        caibroLength = roofExtention + (sin(roofInclination)*((profile.XDim/2)+terca.profile.YDim+(rafter.profile.XDim/2)))/cos(roofInclination)

        caibrosSpacing = length/((nCaibros/2)-1)

        zPos = cos(roofInclination)*((profile.XDim/2)+terca.profile.YDim+(rafter.profile.XDim/2))

        if i < nCaibros/2:
            xPos = - (sin(roofInclination)*((profile.XDim/2)+terca.profile.YDim+(rafter.profile.XDim/2)))/cos(roofInclination)
            yPos = caibrosSpacing*i
            rotation = 90 - degrees(roofInclination)

        else:
            xPos = width + (sin(roofInclination)*((profile.XDim/2)+terca.profile.YDim+(rafter.profile.XDim/2)))/cos(roofInclination)
            yPos = caibrosSpacing*(i-(nCaibros/2))
            rotation = 270 + degrees(roofInclination)


        return IFCMember(ifcFile, profile = profile, name="Caibro" , height=caibroLength, mat="Default", trans=Transform(pos=[xPos , yPos, 4.0 + zPos],rot=[0.0, rotation, 0.0]))

    def GenerateRipa(self, ifcFile, mat, i, width, length, nRipas, rafter, terca, caibro, roofExtention, roofInclination):

        if mat.GetCategory() == "wood":
            profile = ifcFile.GetInstance().create_entity("IfcRectangleProfileDef", ProfileType="AREA", XDim=constants.xCaibro, YDim=constants.yCaibro)

        ripaSpacing = roofExtention/(((nRipas+4)/2)-1)

        if i < nRipas/2:
            xPos = cos(roofInclination)*(ripaSpacing)*(i+1)
            zPos = (profile.YDim/2 + caibro.profile.XDim +terca.profile.YDim+(rafter.profile.XDim/2))/cos(roofInclination) + sin(roofInclination)*(ripaSpacing)*(i+1)
            rotation = - degrees(roofInclination)

        else:
            xPos = width - cos(roofInclination)*(ripaSpacing)*(nRipas - i)
            zPos = (profile.YDim/2 + caibro.profile.XDim +terca.profile.YDim+(rafter.profile.XDim/2))/cos(roofInclination) + sin(roofInclination)*(ripaSpacing)*(nRipas-i)
            rotation = degrees(roofInclination)
            
        return IFCMember(ifcFile, profile = profile, name="Ripa" , height=length, mat="Default", trans=Transform(pos=[xPos , 0.0, 4.0 + zPos],rot=[270.0, rotation, 0.0]))



class FinkTruss:
    def __init__(self, ifcFile, mat, width, porticDistancing, inclination):
        self.__distancing = porticDistancing
        self.__width = width
        self.__material = mat
        self.roofIncliationSlope = inclination
        self.__roofInclination = math.atan(inclination/100)
        self.__roofExtention = (width/2)/math.cos(self.__roofInclination)
        self.__ifcFile = ifcFile

    def KnotCoordenates(self, i, evenCheck):
        i += 1

        topChord = self.__espacamentoTerca
        firstTopChord = self.__roofExtention - (self.__nTopChords-1)*topChord
        
        firstBottomChord = self.__roofExtention - self.__nTopChords*self.__espacamentoTerca + (self.__width - 2*math.cos(self.__roofInclination)*(self.__roofExtention - self.__nTopChords*self.__espacamentoTerca))/(self.__nBottomChords+1)
        bottomChord = (self.__width - 2*math.cos(self.__roofInclination)*(self.__roofExtention - self.__nTopChords*self.__espacamentoTerca))/(self.__nBottomChords+1)

        x = 0.0
        z = 0.0
                             
        if evenCheck == True:
            
            if i == 1:
                x = 0.0
                z = 0.0

            if i%2 == 0:
                x = math.cos(self.__roofInclination)*(firstTopChord+(((i/2)-1)*topChord))
                z = math.sin(self.__roofInclination)*(firstTopChord+(((i/2)-1)*topChord))

                if i > math.floor(self.__nKnots/2):
                    tempI = self.__nKnots + 1 - i

                    x = self.__width - (math.cos(self.__roofInclination)*(firstTopChord+(((tempI/2)-1)*topChord)))
                    z = math.sin(self.__roofInclination)*(firstTopChord+(((tempI/2)-1)*topChord))             
                    
            if i%4 == 1 and i!=1:
                x = firstBottomChord + bottomChord + ((i-5)/4)*bottomChord
                z = 0.0

                if i > math.ceil(self.__nKnots/2):
                    tempI = self.__nKnots + 1 - i

                    x = self.__width - (math.cos(self.__roofInclination)*(firstTopChord+topChord)+((tempI-7)/4)*(math.cos(self.__roofInclination)*(2*topChord))+bottomChord)
                    z = math.sin(self.__roofInclination)*(firstTopChord+topChord)+((tempI-7)/4)*(math.sin(self.__roofInclination)*(2*topChord))

            if i%4 == 3 and i!=self.__nKnots:
                x = math.cos(self.__roofInclination)*(firstTopChord+topChord)+((i-7)/4)*(math.cos(self.__roofInclination)*(2*topChord))+bottomChord
                z = math.sin(self.__roofInclination)*(firstTopChord+topChord)+((i-7)/4)*(math.sin(self.__roofInclination)*(2*topChord))

                if i==3:
                    z = 0.0

                if i > math.ceil(self.__nKnots/2):
                    tempI = self.__nKnots + 1 - i

                    x = self.__width - (firstBottomChord + bottomChord + ((tempI-5)/4)*bottomChord)
                    z = 0.0
                                         
            if i == self.__nKnots:
                x = self.__width
                z = 0.0

        if evenCheck == False:

            if i == 1:
                x = 0.0
                z = 0.0

            if i%2 == 0:
                x = math.cos(self.__roofInclination)*(firstTopChord+(((i/2)-1)*topChord))
                z = math.sin(self.__roofInclination)*(firstTopChord+(((i/2)-1)*topChord))

                if i > math.floor(self.__nKnots/2):
                    tempI = self.__nKnots + 1 - i

                    x = self.__width - (math.cos(self.__roofInclination)*(firstTopChord+(((tempI/2)-1)*topChord)))
                    z = math.sin(self.__roofInclination)*(firstTopChord+(((tempI/2)-1)*topChord))

            if i%4 == 1 and i != 1:
                hipotenusaDireita=((math.sin(self.__roofInclination)*(firstTopChord+(topChord*((i-5)/4)*2)))*math.sqrt((math.sin(self.__roofInclination)*(firstTopChord+((math.floor(i/4)*2)*topChord)))**2+(math.cos(self.__roofInclination)*(firstTopChord+((math.floor(i/4)*2)*topChord))-(firstBottomChord+((((i-5)/4))*bottomChord)))**2))/(math.sin(self.__roofInclination)*(firstTopChord+((math.floor(i/4)*2)*topChord)))
                catetoDireito=math.sqrt((hipotenusaDireita**2)-(math.sin(self.__roofInclination)*(firstTopChord+(topChord*((i-5)/4)*2)))**2)


                x = math.cos(self.__roofInclination)*(firstTopChord+(topChord*((i-5)/4)*2)) + firstBottomChord+(bottomChord*((i-5)/4))-(math.cos(self.__roofInclination)*(firstTopChord+(topChord*((i-5)/4)*2)))+catetoDireito
                z = math.sin(self.__roofInclination)*firstTopChord+((i-5)/4)*(math.sin(self.__roofInclination)*(2*topChord))

                if i > math.ceil(self.__nKnots/2):
                    tempI = self.__nKnots + 1 - i
                    
                    x = self.__width - (firstBottomChord + (math.floor(tempI/4)*bottomChord))
                    z = 0.0

            if i%4 == 3 and i != self.__nKnots:
                x = firstBottomChord + math.floor(i/4)*bottomChord
                z = 0.0

                if i > math.ceil(self.__nKnots/2):
                    tempI = self.__nKnots + 1 - i

                    hipotenusaDireita=((math.sin(self.__roofInclination)*(firstTopChord+(topChord*((tempI-5)/4)*2)))*math.sqrt((math.sin(self.__roofInclination)*(firstTopChord+((math.floor(tempI/4)*2)*topChord)))**2+(math.cos(self.__roofInclination)*(firstTopChord+((math.floor(tempI/4)*2)*topChord))-(firstBottomChord+((((tempI-5)/4))*bottomChord)))**2))/(math.sin(self.__roofInclination)*(firstTopChord+((math.floor(tempI/4)*2)*topChord)))
                    catetoDireito=math.sqrt((hipotenusaDireita**2)-(math.sin(self.__roofInclination)*(firstTopChord+(topChord*((tempI-5)/4)*2)))**2)
                    
                    x = self.__width - (math.cos(self.__roofInclination)*(firstTopChord+(topChord*((tempI-5)/4)*2)) + firstBottomChord+(bottomChord*((tempI-5)/4))-(math.cos(self.__roofInclination)*(firstTopChord+(topChord*((tempI-5)/4)*2)))+catetoDireito)
                    z = math.sin(self.__roofInclination)*firstTopChord+((tempI-5)/4)*(math.sin(self.__roofInclination)*(2*topChord))

            if i == self.__nKnots:
                x = self.__width
                z = 0.0

        
        return [x,z]

    def KnotForces(self):

        if self.__material.GetCategory()=="wood":
           supportLoad = structural.WoodKnotSupportLoad(self.__espacamentoTerca, self.__distancing, temp.weightRoofTiles, self.__material)

        matrix = [[0,0] for a in range(self.__nKnots)]

        for i in range(self.__nKnots):
            if i%2 != 0:
                matrix[i] = [0, supportLoad]
            if i == 0 or i == self.__nKnots - 1:
                matrix[i] = [0, supportLoad/2]
                
        return matrix

    def GenerateRestrictionMatrixRestrictions(self):
        return [[0, 1, 1],
                [self.__nKnots - 1, 0, 1]]

    def ElementsConectivity(self, i, evenCheck):
        
        i += 1
        nKnots = self.__nKnots - 1

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
            if (i-7)%3 == 0 and i>5 and i<=self.__nChords-5:
                firstKnot = 4 + 4*((i-7)/3)
                secondKnot = firstKnot + 4

                if i > math.ceil(self.__nChords/2):
                    firstKnot += 2;
                    secondKnot = firstKnot + 4
                
                if i == math.ceil(self.__nChords/2):
                    secondKnot += 2

            #elementos superiores
            if (i-6)%3 == 0 and i>5 and i<=self.__nChords-5:
                firstKnot = 5 + 4*((i-6)/3)
                secondKnot = firstKnot + 2

            if (i-8)%3 == 0 and i>5 and i<=self.__nChords-5:
                firstKnot = 7 + 4*((i-8)/3)
                secondKnot = firstKnot + 2

            #últimos cinco elementos inferiores e superiores
            if i <= self.__nChords-1 and i > self.__nChords-5:
                tempI= self.__nChords - i

                firstKnot = nKnots - (tempI + 1)
                secondKnot = nKnots - (tempI - 1)

            if i == self.__nChords:
                firstKnot = nKnots - 1
                secondKnot = nKnots

            #diagonais
            if (i-self.__nChords)%5 == 1 and i>self.__nChords:
                firstKnot = 1 + 4*((i-self.__nChords-1)/5)
                secondKnot = firstKnot+1

                if i > math.ceil((self.__nElements - self.__nChords)/2)+self.__nChords:
                    tempI = self.__nElements + 1 - i

                    secondKnot = nKnots - (3 + 4*((tempI-4)/5))
                    firstKnot = secondKnot - 3
                
            if (i-self.__nChords)%5 == 2 and i>self.__nChords:
                firstKnot = 2 + 4*((i-self.__nChords-2)/5)
                secondKnot = firstKnot+1

                if i > math.ceil((self.__nElements - self.__nChords)/2)+self.__nChords:
                    tempI = self.__nElements + 1 - i

                    firstKnot = nKnots - (4 + 4*((tempI-3)/5))
                    secondKnot = firstKnot + 1

            if (i-self.__nChords)%5 == 3 and i>self.__nChords:
                firstKnot = 3 + 4*((i-self.__nChords-3)/5)
                secondKnot = firstKnot+1

                if i > math.ceil((self.__nElements - self.__nChords)/2)+self.__nChords:
                    tempI = self.__nElements + 1 - i

                    secondKnot = nKnots - (2 + 4*((tempI-2)/5))
                    firstKnot = secondKnot - 1
                    
            if (i-self.__nChords)%5 == 4 and i>self.__nChords:
                firstKnot = 3 + 4*((i-self.__nChords-4)/5)
                secondKnot = firstKnot+3

                if i > math.ceil((self.__nElements - self.__nChords)/2)+self.__nChords:
                    tempI = self.__nElements + 1 - i

                    firstKnot = nKnots - (2 + 4*((tempI-1)/5))
                    secondKnot = firstKnot+1
                    
            if (i-self.__nChords)%5 == 0 and i>self.__nChords:
                firstKnot = 4 + 4*((i-self.__nChords-5)/5)
                secondKnot = firstKnot+2

                if i > math.ceil((self.__nElements - self.__nChords)/2)+self.__nChords:
                    tempI = self.__nElements + 1 - i

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
            if (i-5)%3 == 0 and i>3 and i<=self.__nChords-3:
                firstKnot = 2 + 4*((i-5)/3)
                secondKnot = firstKnot + 4

                if i > math.ceil(self.__nChords/2):
                    firstKnot += 2;
                    secondKnot = firstKnot + 4
                
                if i == math.ceil(self.__nChords/2):
                    secondKnot += 2

            #elementos superiores
            if (i-4)%3 == 0 and i>3 and i<=self.__nChords-3:
                firstKnot = 3 + 4*((i-4)/3)
                secondKnot = firstKnot + 2

            if (i-6)%3 == 0 and i>3 and i<=self.__nChords-3:
                firstKnot = 5 + 4*((i-6)/3)
                secondKnot = firstKnot + 2

            #últimos três elementos inferiores e superiores
            if i == self.__nChords-1 or i == self.__nChords-2:
                tempI= self.__nChords - i

                firstKnot = nKnots - (tempI + 1)
                secondKnot = nKnots - (tempI - 1)

            if i == self.__nChords:
                firstKnot = nKnots - 1
                secondKnot = nKnots     

            #diagonais
            if (i-self.__nChords)%5 == 1 and i>self.__nChords:
                firstKnot = 1 + 4*((i-self.__nChords-1)/5)
                secondKnot = firstKnot+1

                if i > math.ceil((self.__nElements - self.__nChords)/2)+self.__nChords:
                    tempI = self.__nElements + 1 - i

                    firstKnot = nKnots - (5 + 4*((tempI-5)/5))
                    secondKnot = firstKnot + 1

            if (i-self.__nChords)%5 == 2 and i>self.__nChords:
                firstKnot = 1 + 4*((i-self.__nChords-2)/5)
                secondKnot = firstKnot+3

                if i > math.ceil((self.__nElements - self.__nChords)/2)+self.__nChords:
                    tempI = self.__nElements + 1 - i

                    firstKnot = nKnots - (4 + 4*((tempI-4)/5))
                    secondKnot = firstKnot+1

            if (i-self.__nChords)%5 == 3 and i>self.__nChords:
                firstKnot = 2 + 4*((i-self.__nChords-3)/5)
                secondKnot = firstKnot+2

                if i > math.ceil((self.__nElements - self.__nChords)/2)+self.__nChords:
                    tempI = self.__nElements + 1 - i

                    firstKnot = nKnots - (4 + 4*((tempI-3)/5))
                    secondKnot = firstKnot+2

            if (i-self.__nChords)%5 == 4 and i>self.__nChords:
                firstKnot = 3 + 4*((i-self.__nChords-4)/5)
                secondKnot = firstKnot+1

                if i > math.ceil((self.__nElements - self.__nChords)/2)+self.__nChords:
                    tempI = self.__nElements + 1 - i

                    firstKnot = nKnots - (4 + 4*((tempI-2)/5))
                    secondKnot = firstKnot+3

            if (i-self.__nChords)%5 == 0 and i>self.__nChords:
                firstKnot = 4 + 4*((i-self.__nChords-5)/5)
                secondKnot = firstKnot+1

                if i > math.ceil((self.__nElements - self.__nChords)/2)+self.__nChords:
                    tempI = self.__nElements + 1 - i

                    firstKnot = nKnots - (2 + 4*((tempI-1)/5))
                    secondKnot = firstKnot+1
           
        return [int(firstKnot), int(secondKnot)]
    
    def GenerateTopRafters(self, i, yPos):
 
        if self.__material.GetCategory()=="wood":
                    
                              
            profile = self.__ifcFile.GetInstance().create_entity("IfcRectangleProfileDef", ProfileType="AREA", XDim=0.12, YDim=0.06)
            
            length = self.__roofExtention

           
            if i == 0:
                xPos = 0.0
                rotation = 90 - math.degrees(self.__roofInclination)
            else:
                xPos = self.__width
                rotation = 270 + math.degrees(self.__roofInclination)
                              
            return IFCMember(self.__ifcFile, profile = profile, name="Member", height=length, mat="Default", trans=Transform(pos=[xPos, yPos, 4.0],rot=[0.0, rotation , 0.0]))
        
    def GenerateBottomRafter(self, yPos):

        trussHight = 4

        if self.__material.GetCategory()=="wood":
                                 
            profile = self.__ifcFile.GetInstance().create_entity("IfcRectangleProfileDef", ProfileType="AREA", XDim=0.12, YDim=0.06) 
            
        return IFCMember(self.__ifcFile, profile = profile, name="Member", height=self.__width, mat="Default", trans=Transform(pos=[0.0, yPos, trussHight],rot=[0.0, 90 , 0.0]))

    def GenerateStrut(self, i, yPos, knots, nStruts, conectivity, evenCheck):

        trussHight = 4
        strutId = i + 1
        matrixId = i + self.__nChords

        xFirstKnot = knots[conectivity[matrixId][0]][0]
        zfirstKnot = knots[conectivity[matrixId][0]][1]

        xSecondKnot = knots[conectivity[matrixId][1]][0]
        zSecondKnot = knots[conectivity[matrixId][1]][1]

        if self.__material.GetCategory() == "wood":
            profile = self.__ifcFile.GetInstance().create_entity("IfcRectangleProfileDef", ProfileType="AREA", XDim=0.12, YDim=0.06)

        if evenCheck == True:

            if strutId%5 == 1 and strutId <= nStruts/2 or strutId%5 == 3 and strutId <= nStruts/2:
                length = math.sqrt((zfirstKnot-zSecondKnot)**2+(xSecondKnot-xFirstKnot)**2)
                xPos = xSecondKnot
                zPos = zSecondKnot
                rotation = 270 + math.degrees(math.atan((zfirstKnot-zSecondKnot)/(xSecondKnot-xFirstKnot)))

            if strutId%5 == 2 and strutId <= nStruts/2 or strutId%5 == 0 and strutId <= nStruts/2:
                length = math.sqrt((zSecondKnot-zfirstKnot)**2+(xSecondKnot-xFirstKnot)**2)
                xPos = xFirstKnot
                zPos = zfirstKnot
                rotation = 90 - math.degrees(math.atan((zSecondKnot-zfirstKnot)/(xSecondKnot-xFirstKnot)))

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
                rotation = 90 - math.degrees(math.atan((zSecondKnot-zfirstKnot)/(xSecondKnot-xFirstKnot)))

            if strutId%5 == 3 and strutId > nStruts/2 or strutId%5 == 0 and strutId > nStruts/2:
                length = math.sqrt((zfirstKnot-zSecondKnot)**2+(xSecondKnot-xFirstKnot)**2)
                xPos = xSecondKnot
                zPos = zSecondKnot
                rotation = 270 + math.degrees(math.atan((zfirstKnot-zSecondKnot)/(xSecondKnot-xFirstKnot)))

        if evenCheck == False:

            if strutId%5 == 1 and strutId <= nStruts/2 or strutId%5 == 4 and strutId <= nStruts/2:
                length = math.sqrt((zfirstKnot-zSecondKnot)**2+(xSecondKnot-xFirstKnot)**2)
                xPos = xSecondKnot
                zPos = zSecondKnot
                rotation = 270 + math.degrees(math.atan((zfirstKnot-zSecondKnot)/(xSecondKnot-xFirstKnot)))

            if strutId%5 == 2 and strutId <= nStruts/2:
                length = xSecondKnot - xFirstKnot
                xPos = xFirstKnot
                zPos = zfirstKnot
                rotation = 90

            if strutId%5 == 3 and strutId <= nStruts/2 or strutId%5 == 0 and strutId <= nStruts/2:
                length = math.sqrt((zSecondKnot-zfirstKnot)**2+(xSecondKnot-xFirstKnot)**2)
                xPos = xFirstKnot
                zPos = zfirstKnot
                rotation = 90 - math.degrees(math.atan((zSecondKnot-zfirstKnot)/(xSecondKnot-xFirstKnot)))

            if strutId%5 == 1 and strutId > nStruts/2 or strutId%5 == 3 and strutId > nStruts/2:
                length = math.sqrt((zfirstKnot-zSecondKnot)**2+(xSecondKnot-xFirstKnot)**2)
                xPos = xSecondKnot
                zPos = zSecondKnot
                rotation = 270 + math.degrees(math.atan((zfirstKnot-zSecondKnot)/(xSecondKnot-xFirstKnot)))

            if strutId%5 == 2 and strutId > nStruts/2 or strutId%5 == 0 and strutId > nStruts/2:
                length = math.sqrt((zSecondKnot-zfirstKnot)**2+(xSecondKnot-xFirstKnot)**2)
                xPos = xFirstKnot
                zPos = zfirstKnot
                rotation = 90 - math.degrees(math.atan((zSecondKnot-zfirstKnot)/(xSecondKnot-xFirstKnot)))

            if strutId%5 == 4 and strutId > nStruts/2:
                length = xSecondKnot - xFirstKnot
                xPos = xFirstKnot
                zPos = zfirstKnot
                rotation = 90

        return IFCMember(self.__ifcFile, profile = profile, name = "Member", height=length, mat="Default", trans=Transform(pos=[xPos, yPos, trussHight + zPos],rot=[0.0, rotation , 0.0]))

    def GenerateRoofScisor(self, yPos):
        
        self.__nTopChords = math.floor(self.__roofExtention/constants.espacamentoMinimoTerca)
            
        #decide o espacamento das tercas a partir do tamanho da perna da tesoura

        #todos os banzos superiores sao iguais e tem tamanho entre 1,3 e 1,65 m
        if self.__roofExtention%constants.espacamentoMinimoTerca<=self.__nTopChords*(constants.espacamentoMaximoTerca-constants.espacamentoMinimoTerca):
            self.__espacamentoTerca=self.__roofExtention/self.__nTopChords
        #Os banzos superiores sao iguais e tem tamanho de 1,65 m, com excess�o ao �ltimo que � maior
        elif self.__roofExtention<=(self.__nTopChords*constants.espacamentoMaximoTerca)+constants.MaximoEspacamentoEspecial:
            self.__espacamentoTerca=constants.espacamentoMaximoTerca
            #espacamentoEspecial=roofExtention-espacamentoTerca*(nTopChords-1)
        #Os banzos superiores sao iguais e tem tamanho de 1,30 m, com excess�o ao �ltimo que � menor
        elif self.__roofExtention%constants.espacamentoMinimoTerca>self.__nTopChords*(constants.espacamentoMaximoTerca-constants.espacamentoMinimoTerca) and self.__roofExtention>(self.__nTopChords*constants.espacamentoMaximoTerca)+constants.MaximoEspacamentoEspecial:
            self.__nTopChords+=1
            self.__espacamentoTerca=constants.espacamentoMinimoTerca
            #espacamentoEspecial=roofExtention%constants.espacamentoMinimoTerca
                          
        #quantidade de banzos inferiores
        self.__nBottomChords=(math.floor(self.__nTopChords/2))*2+1

        self.__nChords = self.__nBottomChords + 2*self.__nTopChords

        #Se o numero de banzos superiores por �gua for par ou impar
        if self.__nTopChords%2==0:
            nStruts=int((2+((self.__nTopChords-2)/2)*5)*2)
            evenCheck = True
        else:
            nStruts=int(math.floor(self.__nTopChords/2)*10)
            evenCheck = False

        self.__nKnots = self.__nTopChords*4 - 1

        self.__nElements = self.__nKnots*2 - 3
                
        self.nos = [self.KnotCoordenates(i, evenCheck) for i in range(self.__nKnots)]

        self.elementos = [self.ElementsConectivity(i, evenCheck) for i in range(self.__nElements)]
        
        banzosSuperiores = [self.GenerateTopRafters(i, yPos) for i in range(2)]
        
        banzoInferior = self.GenerateBottomRafter(yPos)
        
        diagonais = [self.GenerateStrut(i, yPos, self.nos,  nStruts, self.elementos, evenCheck) for i in range(nStruts)]
        
        return [banzosSuperiores, banzoInferior, diagonais]
    
    def GetRoofInclination(self):
        return self.__roofInclination

    def GetRoofExtention(self):
        return self.__roofExtention

    def GetEspacamentoTerca(self):
        return self.__espacamentoTerca

    def GetTopChords(self):
        return self.__nTopChords