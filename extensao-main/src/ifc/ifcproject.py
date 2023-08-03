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
    material = IFCWoodMat(16,350,7,0.8)      
    
    
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
            
        pilares1 = [self.GenerateColumn(ifcFile, self.__material.material, i, 0.1) for i in range((1+math.ceil(self.__structure.length/5)))]
        pilares2 = [self.GenerateColumn(ifcFile, self.__material.material, i, self.__structure.width-0.1) for i in range((1+math.ceil(self.__structure.length/5)))]

        for pilar in pilares1:
            ifcFile.AssignContainer(pilar, building)

        for pilar in pilares2:
            ifcFile.AssignContainer(pilar, building)        

        roofExtention = (self.__structure.width/2)/math.cos(math.atan(float(temp.roofInclination/100)))

        nTopChords = math.floor(roofExtention/constants.espacamentoMinimoTerca)
            
        #decide o espacamento das ter�as a partir do tamanho da perna da tesoura

        #todos os banzos superiores s�o iguais e tem tamanho entre 1,3 e 1,65 m
        if roofExtention%constants.espacamentoMinimoTerca<=nTopChords*(constants.espacamentoMaximoTerca-constants.espacamentoMinimoTerca):
            espacamentoTerca=roofExtention/nTopChords
        #Os banzos superiores s�o iguais e tem tamanho de 1,65 m, com excess�o ao �ltimo que � maior
        elif roofExtention<=(nTopChords*constants.espacamentoMaximoTerca)+constants.MaximoEspacamentoEspecial:
            espacamentoTerca=constants.espacamentoMaximoTerca
            #espacamentoEspecial=roofExtention-espacamentoTerca*(nTopChords-1)
        #Os banzos superiores s�o iguais e tem tamanho de 1,30 m, com excess�o ao �ltimo que � menor
        elif roofExtention%constants.espacamentoMinimoTerca>nTopChords*(constants.espacamentoMaximoTerca-constants.espacamentoMinimoTerca) and roofExtention>(nTopChords*constants.espacamentoMaximoTerca)+constants.MaximoEspacamentoEspecial:
            nTopChords+=1
            espacamentoTerca=constants.espacamentoMinimoTerca
            #espacamentoEspecial=roofExtention%constants.espacamentoMinimoTerca
                    
        #quantidade de banzos inferiores
        nBottomChords=(math.floor(nTopChords/2))*2+1

        #Se o n�mero de banzos superiores por �gua for par ou impar
        if nTopChords%2==0:
            nStruts=int((2+((nTopChords-2)/2)*5)*2)
            evenCheck = True
        else:
            nStruts=int(math.floor(nTopChords/2)*10)
            evenCheck = False

        
        banzosSuperiores = [self.GenerateTopChords(ifcFile, self.__material.material, i, espacamentoTerca, nTopChords, roofExtention, math.atan(temp.roofInclination/100)) for i in range(2*nTopChords)]

        for banzoSuperior in banzosSuperiores:
            ifcFile.AssignContainer(banzoSuperior, building)

        banzosInferiores = [self.GenerateBottomChords(ifcFile, self.__material.material, i, nBottomChords, nTopChords, espacamentoTerca, roofExtention, math.atan(temp.roofInclination/100), self.__structure.width) for i in range(nBottomChords)]
        
        for banzoInferior in banzosInferiores:
            ifcFile.AssignContainer(banzoInferior, building)

        tesoura = [self.GenerateStrut(ifcFile, self.__material.material, i, espacamentoTerca, nBottomChords, nTopChords, self.__structure.width, roofExtention, math.atan(temp.roofInclination/100), nStruts, evenCheck) for i in range(nStruts)]
        
        for membro in tesoura:
            ifcFile.AssignContainer(membro, building)
                      

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
        ifcFile.AddMaterial(IFCWoodMat(16,350,7,0.8) ,     styleClass="IfcSurfaceStyleShading", att={ "SurfaceColour" : { "Name" : None, "Red" : .50, "Green" : .35, "Blue" : .25}, "Transparency" : 0.0 })

        return project

    def GenerateColumn(self, ifcFile, mat, i, xPos):
        
       if mat.GetCategory()=="wood":
           supportLoad = structural.WoodSupportLoad(self.__structure.width, self.__structure.length, temp.weightRoofTiles, temp.roofInclination, temp.montantes, mat)

           profile = ifcFile.GetInstance().create_entity("IfcRectangleProfileDef", ProfileType="AREA", XDim= structural.GetXDimention(supportLoad,mat), YDim=structural.GetYDimention(supportLoad,mat))

           #profile = RectangleProfile(width = structural.GetXDimention(supportLoad,mat), depth = structural.GetYDimention(supportLoad,mat))

           pilarYDistancing = 5

           return IFCColumn(ifcFile, profile = profile, trans=Transform(pos=[xPos, pilarYDistancing*i, 0.0],rot=[0.0, 0.0, 0.0]) )

    def GenerateTopChords(self, ifcFile, mat, i, espacamentoTerca, nTopChords, roofExtention, roofInclination):
 
        trussHight = 4
 
        if mat.GetCategory()=="wood":
                    
                              
            profile = ifcFile.GetInstance().create_entity("IfcRectangleProfileDef", ProfileType="AREA", XDim=0.12, YDim=0.06)
            
            length = espacamentoTerca

            xPos = math.cos(roofInclination)*(roofExtention-espacamentoTerca*(nTopChords-1)) + math.cos(roofInclination)*length*(i-1)

            zPos = trussHight + math.sin(roofInclination)*(roofExtention-espacamentoTerca*(nTopChords-1)) + math.sin(roofInclination)*length*(i-1)
            
            rotation = 90 - degrees(roofInclination)
                                
            if i >= nTopChords:
                rotation = 90 + degrees(roofInclination)
                zPos -= math.sin(roofInclination)*length*(i-nTopChords)*2
                
            if i==0 or i+1==nTopChords*2:
                length=roofExtention-espacamentoTerca*(nTopChords-1)
                zPos = trussHight

            if i==0:
                xPos = 0
                
            if i+1 == nTopChords*2:
                zPos = trussHight + math.sin(roofInclination)*length
                
            
            return IFCMember(ifcFile, profile = profile, name="Member", height=length, mat="Default", trans=Transform(pos=[xPos, 0.0, zPos],rot=[0.0, rotation , 0.0]))

    def GenerateBottomChords(self, ifcFile, mat, i, nBottomChords, nTopChords, espacamentoTerca, roofExtention, roofInclination, width):

        trussHight = 4

        if mat.GetCategory()=="wood":
                                 
            profile = ifcFile.GetInstance().create_entity("IfcRectangleProfileDef", ProfileType="AREA", XDim=0.12, YDim=0.06) 

            #se os banzos iferiores do cantos s�o maiores
            if roofExtention>nTopChords*espacamentoTerca:
                
                InclinatedExcedent=roofExtention-(nTopChords*espacamentoTerca)
                excedent=(InclinatedExcedent)*math.cos(roofInclination)
                length=(width-(excedent*2))/(nBottomChords+1)
                #banzo de canto
                if i==0 or i+1 == nBottomChords:
                    length+=excedent
                #banzo central
                if i+1==math.ceil(nBottomChords/2):
                    length*=2

                xPos =  length*i + excedent

                if i==0:
                    xPos = 0

                if i+1>math.ceil(nBottomChords/2):
                    xPos = (i+1)*length + excedent

                if i+1 == math.ceil(nBottomChords/2):
                    xPos = (length/2)*i + excedent

                if i+1 == nBottomChords:
                    xPos = (i+1)*(length-excedent) + excedent

            #se todos os banzos inferiores s�o iguais
            else:
                
                length=width/(nBottomChords+1)
            #banzo central
                if i+1==math.ceil(nBottomChords/2):
                    length*=2

                xPos =  length*i

                if i+1==math.ceil(nBottomChords/2):
                    xPos = (length/2)*i
            
                if i+1>math.ceil(nBottomChords/2):
                    xPos = (i+1)*length

            return IFCMember(ifcFile, profile = profile, name="Member", height=length, mat="Default", trans=Transform(pos=[xPos, 0.0, trussHight],rot=[0.0, 90 , 0.0]))

    def GenerateStrut(self, ifcFile, mat, i, espacamentoTerca, nBottomChords, nTopChords, width, roofExtention, roofInclination, nStruts, evenCheck):

        name = "Member"

        trussHight = 4
        i+=1

        if mat.GetCategory() == "wood":

            profile = ifcFile.GetInstance().create_entity("IfcRectangleProfileDef", ProfileType="AREA", XDim=0.12, YDim=0.06)
            
            firstTopChord = roofExtention - (nTopChords-1)*espacamentoTerca
            topChord = espacamentoTerca

            firstBottomChord = roofExtention - nTopChords*espacamentoTerca + (width - 2*math.cos(roofInclination)*(roofExtention - nTopChords*espacamentoTerca))/(nBottomChords+1)
            bottomChord = (width - 2*math.cos(roofInclination)*(roofExtention - nTopChords*espacamentoTerca))/(nBottomChords+1)

            
            #localiza a diagonal a partir da identifica��o e calcula o comprimento usando trigonometria b�sica.
            if evenCheck==True:
                
                length=1
                xPos = -10
                rotation = 0
                zPos = 0
                name = "Strut" + str(i)

                if i%5==0 and i<=nStruts/2:
                    length=math.sqrt((math.sin(roofInclination)*(firstTopChord+(((i/5)*2)-1)*topChord))**2+((math.cos(roofInclination)*(firstTopChord+(((i/5)*2)-1)*topChord))-(firstBottomChord+(bottomChord*((i/5)-1))))**2)

                    xPos = firstBottomChord + bottomChord + ((i/5)-1)*bottomChord
                    zPos = 0
                    rotation = 90 - degrees(math.atan((math.sin(roofInclination)*(firstTopChord+(((i/5)*2)-1)*topChord))/((math.cos(roofInclination)*(firstTopChord+(((i/5)*2)-1)*topChord))-(firstBottomChord+(bottomChord*((i/5)-1))))))
                                        
                if (i-1)%5==0 and i<=nStruts/2:
                    length=math.sqrt((math.sin(roofInclination)*firstTopChord)**2+(firstBottomChord-(math.cos(roofInclination))*firstTopChord)**2)
                                                                               
                    xPos=math.cos(roofInclination)*(firstTopChord+topChord)+((i-6)/5)*(math.cos(roofInclination)*(2*topChord))+bottomChord
                    zPos=math.sin(roofInclination)*(firstTopChord+topChord)+((i-6)/5)*(math.sin(roofInclination)*(2*topChord))
                    rotation = 360 - degrees(math.atan((bottomChord-(math.cos(roofInclination))*topChord)/(math.sin(roofInclination)*topChord)))

                    if i == 1:
                        length = math.sqrt((math.sin(roofInclination)*topChord)**2+(bottomChord-(math.cos(roofInclination))*topChord)**2)
                        xPos = firstBottomChord
                        zPos = 0
                        rotation = 360 - degrees(math.atan((firstBottomChord-(math.cos(roofInclination))*firstTopChord)/(math.sin(roofInclination)*firstTopChord)))                                          
                                                      
                if (i-2)%5==0 and i<=nStruts/2:
                    length=math.sqrt((math.sin(roofInclination)*(2*topChord))**2+((math.cos(roofInclination)*(2*topChord))-bottomChord)**2)
                    
                    xPos=math.cos(roofInclination)*(firstTopChord+topChord)+((i-7)/5)*(math.cos(roofInclination)*(2*topChord))+bottomChord
                    zPos=math.sin(roofInclination)*(firstTopChord+topChord)+((i-7)/5)*(math.sin(roofInclination)*(2*topChord))
                    rotation = 90 - degrees(math.atan((math.sin(roofInclination)*(2*topChord))/((math.cos(roofInclination)*(2*topChord))-bottomChord)))

                    if i == 2:
                        length=math.sqrt((math.sin(roofInclination)*(firstTopChord+topChord))**2+((math.cos(roofInclination)*(firstTopChord+topChord))-firstBottomChord)**2)
                        xPos = firstBottomChord
                        zPos = 0
                        rotation = 90 - degrees(math.atan((math.sin(roofInclination)*(firstTopChord + topChord))/((math.cos(roofInclination)*(firstTopChord + topChord))-bottomChord)))
  
                if (i-3)%5==0 and i<=nStruts/2:
                    length=math.sqrt((math.sin(roofInclination)*(firstTopChord+((((i+2)/5)*2)-1)*topChord))**2+((firstBottomChord+((i+2)/5)*bottomChord)-(math.cos(roofInclination)*(firstTopChord+((((i+2)/5)*2)-1)*topChord)))**2)

                    xPos = firstBottomChord + bottomChord + math.floor(i/5)*bottomChord
                    zPos = 0
                    rotation = 270 + degrees(math.atan((math.sin(roofInclination)*(firstTopChord+((((i+2)/5)*2)-1)*topChord))/((firstBottomChord+((i+2)/5)*bottomChord)-(math.cos(roofInclination)*(firstTopChord+((((i+2)/5)*2)-1)*topChord)))))
                                    
                if (i-4)%5==0 and i<=nStruts/2:
                    length=bottomChord

                    xPos = math.cos(roofInclination)*(firstTopChord+topChord) + math.floor(i/5)*(math.cos(roofInclination)*(2*topChord))
                    zPos = math.sin(roofInclination)*(firstTopChord+topChord) + math.floor(i/5)*(math.sin(roofInclination)*(2*topChord))
                    rotation = 90
                                                                 
                if (i-nStruts/2-1)%5==0 and i>nStruts/2:
                    tempI = (nStruts/2+1)-(i-nStruts/2)
                    length=math.sqrt((math.sin(roofInclination)*(firstTopChord+topChord))**2+((math.cos(roofInclination)*(firstTopChord+topChord))-firstBottomChord)**2)    

                    xPos= width - (math.cos(roofInclination)*(firstTopChord+topChord)+((tempI-7)/5)*(math.cos(roofInclination)*(2*topChord))+bottomChord)
                    zPos= math.sin(roofInclination)*(firstTopChord+topChord)+((tempI-7)/5)*(math.sin(roofInclination)*(2*topChord))
                    rotation = 270 + degrees(math.atan((math.sin(roofInclination)*(2*topChord))/((math.cos(roofInclination)*(2*topChord))-bottomChord)))

                    if tempI == 2:
                        length=math.sqrt((math.sin(roofInclination)*(firstTopChord+topChord))**2+((math.cos(roofInclination)*(firstTopChord+topChord))-firstBottomChord)**2)
                        xPos = width - firstBottomChord
                        zPos = 0
                        rotation = 270 + degrees(math.atan((math.sin(roofInclination)*(firstTopChord + topChord))/((math.cos(roofInclination)*(firstTopChord + topChord))-bottomChord)))

                if (i-nStruts/2-2)%5==0 and i>nStruts/2:
                    tempI = (nStruts/2+1)-(i-nStruts/2)
                    length=math.sqrt((math.sin(roofInclination)*firstTopChord)**2+(firstBottomChord-(math.cos(roofInclination))*firstTopChord)**2)

                    xPos=width - (math.cos(roofInclination)*(firstTopChord+topChord)+((tempI-6)/5)*(math.cos(roofInclination)*(2*topChord))+bottomChord)
                    zPos=math.sin(roofInclination)*(firstTopChord+topChord)+((tempI-6)/5)*(math.sin(roofInclination)*(2*topChord))
                    rotation = degrees(math.atan((bottomChord-(math.cos(roofInclination))*topChord)/(math.sin(roofInclination)*topChord)))

                    if tempI == 1:
                        length = math.sqrt((math.sin(roofInclination)*topChord)**2+(bottomChord-(math.cos(roofInclination))*topChord)**2)
                        xPos = width - firstBottomChord
                        zPos = 0
                        rotation = degrees(math.atan((firstBottomChord-(math.cos(roofInclination))*firstTopChord)/(math.sin(roofInclination)*firstTopChord)))

                if (i-nStruts/2-3)%5==0 and i>nStruts/2:
                    tempI=(nStruts/2+3)-(5*math.ceil((i-nStruts/2)/5))
                    length=math.sqrt((math.sin(roofInclination)*(firstTopChord+(((tempI/5)*2)-1)*topChord))**2+((math.cos(roofInclination)*(firstTopChord+(((tempI/5)*2)-1)*topChord))-(firstBottomChord+(bottomChord*((tempI/5)-1))))**2)

                    xPos = width - (firstBottomChord + bottomChord + ((tempI/5)-1)*bottomChord)
                    zPos = 0
                    rotation = 270 + degrees(math.atan((math.sin(roofInclination)*(firstTopChord+(((tempI/5)*2)-1)*topChord))/((math.cos(roofInclination)*(firstTopChord+(((tempI/5)*2)-1)*topChord))-(firstBottomChord+(bottomChord*((tempI/5)-1))))))

                if (i-nStruts/2-4)%5==0 and i>nStruts/2:
                    tempI=(nStruts/2)-(i-nStruts/2)
                    length=bottomChord

                    xPos = width - (math.cos(roofInclination)*(firstTopChord+topChord) + math.floor(tempI/5)*(math.cos(roofInclination)*(2*topChord)))
                    zPos = math.sin(roofInclination)*(firstTopChord+topChord) + math.floor(tempI/5)*(math.sin(roofInclination)*(2*topChord))
                    rotation = 270

                if (i-nStruts/2)%5==0 and i>nStruts/2:
                    tempI = (nStruts/2+1)-(i-nStruts/2)
                    length = math.sqrt((math.sin(roofInclination)*(firstTopChord+((((tempI+2)/5)*2)-1)*topChord))**2+((firstBottomChord+((tempI+2)/5)*bottomChord)-(math.cos(roofInclination)*(firstTopChord+((((tempI+2)/5)*2)-1)*topChord)))**2)

                    xPos = width - (firstBottomChord + bottomChord + math.floor(tempI/5)*bottomChord)
                    zPos = 0
                    rotation = 90 - degrees(math.atan((math.sin(roofInclination)*(firstTopChord+((((tempI+2)/5)*2)-1)*topChord))/((firstBottomChord+((tempI+2)/5)*bottomChord)-(math.cos(roofInclination)*(firstTopChord+((((tempI+2)/5)*2)-1)*topChord)))))

            if evenCheck==False:

                if i%5==0 and i<=nStruts/2:
                     catetoOpostoMaior=math.sin(roofInclination)*(firstTopChord+(((i/5)*2)*topChord))
                     hipotenusaMaior=math.sqrt(catetoOpostoMaior**2+(math.cos(roofInclination)*(firstTopChord+((math.ceil(i/5)*2)*topChord))-(firstBottomChord+((i/5)-1)*bottomChord))**2)
                     hipotenusaMenor=(math.sin(roofInclination)*(firstTopChord+(topChord*((i/5)-1)*2))*hipotenusaMaior)/catetoOpostoMaior
                     length=hipotenusaMaior-hipotenusaMenor 

                     hipotenusaDireita=((math.sin(roofInclination)*(firstTopChord+(topChord*((i/5)-1)*2)))*math.sqrt((math.sin(roofInclination)*(firstTopChord+(((i/5)*2)*topChord)))**2+(math.cos(roofInclination)*(firstTopChord+(((i/5)*2)*topChord))-(firstBottomChord+(((i/5)-1)*bottomChord)))**2))/(math.sin(roofInclination)*(firstTopChord+(((i/5)*2)*topChord)))
                     catetoDireito=math.sqrt((hipotenusaDireita**2)-(math.sin(roofInclination)*(firstTopChord+(topChord*((i/5)-1)*2)))**2)

                     xPos = math.cos(roofInclination)*(firstTopChord+(topChord*((i/5)-1)*2)) + firstBottomChord+(bottomChord*((i/5)-1))-(math.cos(roofInclination)*(firstTopChord+(topChord*((i/5)-1)*2)))+catetoDireito
                     zPos = math.sin(roofInclination)*(firstTopChord+(topChord*((i/5)-1)*2))
                     #rotation = 90 - degrees(math.atan((math.sin(roofInclination)*(firstTopChord+(((i-2)/5)*2)*topChord))/(firstBottomChord+((((i-2)/5)-1)*bottomChord))))
                     rotation = degrees(math.acos(catetoOpostoMaior/hipotenusaMaior))

                if (i-1)%5==0 and i<=nStruts/2:
                    length=math.sqrt((math.sin(roofInclination)*(firstTopChord+(((i-1)/5)*2)*topChord))**2+((firstBottomChord+(((i-1)/5))*bottomChord)-(math.cos(roofInclination)*(firstTopChord+(((i-1)/5)*2)*topChord)))**2)
                    xPos=firstBottomChord+(((i-1)/5))*bottomChord
                    zPos=0
                    rotation = 270 + degrees(math.atan((math.sin(roofInclination)*(firstTopChord+(((i-1)/5)*2)*topChord))/((firstBottomChord+(((i-1)/5))*bottomChord)-(math.cos(roofInclination)*(firstTopChord+(((i-1)/5)*2)*topChord)))))
                    
                if (i-2)%5==0 and i<=nStruts/2:
                    hipotenusaDireita=((math.sin(roofInclination)*(firstTopChord+(topChord*math.floor(i/5)*2)))*math.sqrt((math.sin(roofInclination)*(firstTopChord+((math.ceil(i/5)*2)*topChord)))**2+(math.cos(roofInclination)*(firstTopChord+((math.ceil(i/5)*2)*topChord))-(firstBottomChord+((math.floor(i/5))*bottomChord)))**2))/(math.sin(roofInclination)*(firstTopChord+((math.ceil(i/5)*2)*topChord)))
                    catetoDireito=math.sqrt((hipotenusaDireita**2)-(math.sin(roofInclination)*(firstTopChord+(topChord*math.floor(i/5)*2)))**2)
                    length=firstBottomChord+(bottomChord*math.floor(i/5))-(math.cos(roofInclination)*(firstTopChord+(topChord*math.floor(i/5)*2)))+catetoDireito

                    xPos = math.cos(roofInclination)*(firstTopChord+(topChord*math.floor(i/5)*2))
                    zPos = math.sin(roofInclination)*(firstTopChord+(topChord*math.floor(i/5)*2))
                    rotation = 90
                    
                if (i-3)%5==0 and i<=nStruts/2:
                    catetoOpostoMaior=math.sin(roofInclination)*(firstTopChord+((math.ceil(i/5)*2)*topChord))
                    hipotenusaMaior=math.sqrt(catetoOpostoMaior**2+(math.cos(roofInclination)*(firstTopChord+((math.ceil(i/5)*2)*topChord))-(firstBottomChord+((math.floor(i/5))*bottomChord)))**2)
                    length=((math.sin(roofInclination)*(firstTopChord+(topChord*math.floor(i/5)*2)))*hipotenusaMaior)/catetoOpostoMaior
                    xPos=firstBottomChord+(math.floor(i/5))*bottomChord
                    zPos = 0
                    #rotation = 90 - degrees(math.atan((math.sin(roofInclination)*(firstTopChord+((math.ceil(i/5)*2)*topChord)))/(math.cos(roofInclination)*(firstTopChord+((math.ceil(i/5)*2)*topChord))-xPos)))
                    rotation = degrees(math.acos(catetoOpostoMaior/hipotenusaMaior))

                if (i-4)%5==0 and i<=nStruts/2:
                    hipotenusaDireita=((math.sin(roofInclination)*(firstTopChord+(topChord*math.floor(i/5)*2)))*math.sqrt((math.sin(roofInclination)*(firstTopChord+((math.ceil(i/5)*2)*topChord)))**2+(math.cos(roofInclination)*(firstTopChord+((math.ceil(i/5)*2)*topChord))-(firstBottomChord+((math.floor(i/5))*bottomChord)))**2))/(math.sin(roofInclination)*(firstTopChord+((math.ceil(i/5)*2)*topChord)))
                    catetoDireito=math.sqrt((hipotenusaDireita**2)-(math.sin(roofInclination)*(firstTopChord+(topChord*math.floor(i/5)*2)))**2)
                    catetoOposto=math.sin(roofInclination)*topChord
                    catetoAdjascente=firstBottomChord+(bottomChord*math.floor(i/5))-(math.cos(roofInclination)*(firstTopChord+(topChord*math.floor(i/5)*2)))+catetoDireito-(math.cos(roofInclination)*topChord)
                    length=math.sqrt(catetoOposto**2+catetoAdjascente**2)
                    xPos = math.cos(roofInclination)*(firstTopChord+(topChord*math.floor(i/5)*2)) + firstBottomChord+(bottomChord*math.floor(i/5))-(math.cos(roofInclination)*(firstTopChord+(topChord*math.floor(i/5)*2)))+catetoDireito
                    zPos = math.sin(roofInclination)*(firstTopChord+(topChord*math.floor(i/5)*2))
                    #rotation = 270 + degrees(math.atan((math.sin(roofInclination)*topChord)/(xPos - math.cos(roofInclination)*(firstTopChord+topChord*math.floor(i/5)*2+topChord))))
                    rotation = 270 + degrees(math.atan(catetoOposto/catetoAdjascente))

                if (i-nStruts/2)%5==0 and i>nStruts/2:
                    tempI=(nStruts/2+1)-(i-nStruts/2)
                    length=math.sqrt((math.sin(roofInclination)*(firstTopChord+(((tempI-1)/5)*2)*topChord))**2+((firstBottomChord+(((tempI-1)/5))*bottomChord)-(math.cos(roofInclination)*(firstTopChord+(((tempI-1)/5)*2)*topChord)))**2)

                    xPos = width - (firstBottomChord + bottomChord*math.floor(tempI/5))
                    zPos = 0
                    rotation = 90 - degrees(math.atan((math.sin(roofInclination)*(firstTopChord+(((tempI-1)/5)*2)*topChord))/((firstBottomChord+(((tempI-1)/5))*bottomChord)-(math.cos(roofInclination)*(firstTopChord+(((tempI-1)/5)*2)*topChord)))))
                    
                if (i-nStruts/2-1)%5==0 and i>nStruts/2:
                    tempI=(nStruts/2)-(5*math.floor((i-nStruts/2)/5))
                    catetoOpostoMaior=math.sin(roofInclination)*(firstTopChord+((math.ceil(tempI/5)*2)*topChord))
                    hipotenusaMaior=math.sqrt(catetoOpostoMaior**2+(math.cos(roofInclination)*(firstTopChord+((math.ceil(tempI/5)*2)*topChord))-(firstBottomChord+((tempI/5)-1)*bottomChord))**2)
                    hipotenusaMenor=(math.sin(roofInclination)*(firstTopChord+(topChord*((tempI/5)-1)*2))*hipotenusaMaior)/catetoOpostoMaior
                    length=hipotenusaMaior-hipotenusaMenor

                    hipotenusaDireita=((math.sin(roofInclination)*(firstTopChord+(topChord*((tempI/5)-1)*2)))*math.sqrt((math.sin(roofInclination)*(firstTopChord+(((tempI/5)*2)*topChord)))**2+(math.cos(roofInclination)*(firstTopChord+(((tempI/5)*2)*topChord))-(firstBottomChord+(((tempI/5)-1)*bottomChord)))**2))/(math.sin(roofInclination)*(firstTopChord+(((tempI/5)*2)*topChord)))
                    catetoDireito=math.sqrt((hipotenusaDireita**2)-(math.sin(roofInclination)*(firstTopChord+(topChord*((tempI/5)-1)*2)))**2)

                    xPos = width - (math.cos(roofInclination)*(firstTopChord+(topChord*((tempI/5)-1)*2)) + firstBottomChord+(bottomChord*((tempI/5)-1))-(math.cos(roofInclination)*(firstTopChord+(topChord*((tempI/5)-1)*2)))+catetoDireito)
                    zPos = math.sin(roofInclination)*(firstTopChord+(topChord*((tempI/5)-1)*2))
                    #rotation = 270 + degrees(math.atan((math.sin(roofInclination)*(firstTopChord+((tempI/5)*2)*topChord))/(firstBottomChord+(((tempI/5)-1)*bottomChord))))
                    rotation = 360 - degrees(math.acos(catetoOpostoMaior/hipotenusaMaior))
                   
                if (i-nStruts/2-2)%5==0 and i>nStruts/2:
                    tempI=(nStruts/2+4)-(5*math.ceil((i-nStruts/2)/5))
                    hipotenusaDireita=((math.sin(roofInclination)*(firstTopChord+(topChord*math.floor(tempI/5)*2)))*math.sqrt((math.sin(roofInclination)*(firstTopChord+((math.ceil(tempI/5)*2)*topChord)))**2+(math.cos(roofInclination)*(firstTopChord+((math.ceil(tempI/5)*2)*topChord))-(firstBottomChord+((math.floor(tempI/5))*bottomChord)))**2))/(math.sin(roofInclination)*(firstTopChord+((math.ceil(tempI/5)*2)*topChord)))
                    catetoDireito=math.sqrt((hipotenusaDireita**2)-(math.sin(roofInclination)*(firstTopChord+(topChord*math.floor(tempI/5)*2)))**2)
                    catetoOposto=math.sin(roofInclination)*topChord
                    catetoAdjascente=firstBottomChord+(bottomChord*math.floor(tempI/5))-(math.cos(roofInclination)*(firstTopChord+(topChord*math.floor(tempI/5)*2)))+catetoDireito-(math.cos(roofInclination)*topChord)
                    length=math.sqrt(catetoOposto**2+catetoAdjascente**2)

                    xPos = width - (math.cos(roofInclination)*(firstTopChord+(topChord*math.floor(tempI/5)*2)) + firstBottomChord+(bottomChord*math.floor(tempI/5))-(math.cos(roofInclination)*(firstTopChord+(topChord*math.floor(tempI/5)*2)))+catetoDireito)
                    zPos = math.sin(roofInclination)*(firstTopChord+(topChord*math.floor(tempI/5)*2))
                    #rotation = degrees(math.atan((math.sin(roofInclination)*topChord)/(xPos - math.cos(roofInclination)*(firstTopChord+topChord*math.floor(tempI/5)*2+topChord))))
                    rotation = 90 - degrees(math.atan(catetoOposto/catetoAdjascente))
            
                if (i-nStruts/2-3)%5==0 and i>nStruts/2:
                    tempI=(nStruts/2+3)-(5*math.ceil((i-nStruts/2)/5))
                    catetoOpostoMaior=math.sin(roofInclination)*(firstTopChord+((math.ceil(tempI/5)*2)*topChord))
                    hipotenusaMaior=math.sqrt(catetoOpostoMaior**2+(math.cos(roofInclination)*(firstTopChord+((math.ceil(tempI/5)*2)*topChord))-(firstBottomChord+((math.floor(tempI/5))*bottomChord)))**2)
                    length=((math.sin(roofInclination)*(firstTopChord+(topChord*math.floor(tempI/5)*2)))*hipotenusaMaior)/catetoOpostoMaior

                    xPos= width - (firstBottomChord+(math.floor(tempI/5))*bottomChord)
                    zPos = 0
                    #rotation = 270 - degrees(math.atan((math.sin(roofInclination)*(firstTopChord+((math.ceil(tempI/5)*2)*topChord)))/(math.cos(roofInclination)*(firstTopChord+((math.ceil(tempI/5)*2)*topChord))-xPos)))
                    rotation = 360 - degrees(math.acos(catetoOpostoMaior/hipotenusaMaior))

                if (i-nStruts/2-4)%5==0 and i>nStruts/2:
                    tempI=(nStruts/2+2)-(5*math.ceil((i-nStruts/2)/5))
                    hipotenusaDireita=((math.sin(roofInclination)*(firstTopChord+(topChord*math.floor(tempI/5)*2)))*math.sqrt((math.sin(roofInclination)*(firstTopChord+((math.ceil(tempI/5)*2)*topChord)))**2+(math.cos(roofInclination)*(firstTopChord+((math.ceil(tempI/5)*2)*topChord))-(firstBottomChord+((math.floor(tempI/5))*bottomChord)))**2))/(math.sin(roofInclination)*(firstTopChord+((math.ceil(tempI/5)*2)*topChord)))
                    catetoDireito=math.sqrt((hipotenusaDireita**2)-(math.sin(roofInclination)*(firstTopChord+(topChord*math.floor(tempI/5)*2)))**2)
                    length=firstBottomChord+(bottomChord*math.floor(tempI/5))-(math.cos(roofInclination)*(firstTopChord+(topChord*math.floor(tempI/5)*2)))+catetoDireito

                    xPos = width - (math.cos(roofInclination)*(firstTopChord+(topChord*math.floor(tempI/5)*2)))
                    zPos = math.sin(roofInclination)*(firstTopChord+(topChord*math.floor(tempI/5)*2))
                    rotation = 270



            if i==1:
                length=math.sqrt((math.sin(roofInclination)*firstTopChord)**2+(firstBottomChord-(math.cos(roofInclination))*firstTopChord)**2)

        return IFCMember(ifcFile, profile = profile, name = name, height=length, mat="Default", trans=Transform(pos=[xPos, 0.0, trussHight + zPos],rot=[0.0, rotation , 0.0]))


