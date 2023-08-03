import math
import sys

sys.path.append("../definitions")
from definitions import constants

def CollumnDistancing(mat):
    if mat.GetCategory()=="wood":
        return constants.maximumColumnDistanceWood
    elif mat.GetCategory()=="steel":
        return constants.maximumCollumnDistanceSteel

def WoodSupportLoad(width, length, weightRoofTiles, roofInclination, distanceRoofSupport, material):

        distance = length/math.ceil(length/CollumnDistancing(material))

        inclinationInRadians=math.atan(float(roofInclination)/100)
        cossin = math.cos(inclinationInRadians)

        if length<=5:
            InfluenceArea=(float(length)/2)*((width/2)*(cossin))
        else:
            InfluenceArea=float(distance)*((float(width)/2)*(cossin))
                    
        espacamentoTerca=cossin*distanceRoofSupport
                
        weightStructure=material.GetMaterialWeight()*((constants.sessaoRipa/constants.espacamentoRipa)+(constants.sessaoCaibro/constants.espacamentoCaibro)+(constants.sessaoTerca/espacamentoTerca))
        return (weightStructure+weightRoofTiles)*InfluenceArea


def GetXDimention(load, material):

        if material.GetRelativeHumidity() <= 0.65:
            kmod2 = 1.0
        elif material.GetRelativeHumidity() > 0.65 and material.GetRelativeHumidity() <= 0.75:
            kmod2 = 0.9
        elif material.GetRelativeHumidity() > 0.75 and material.GetRelativeHumidity() <= 0.85:
            kmod2 = 0.8
        elif material.GetRelativeHumidity() > 0.75:
            kmod2 = 0.7

        kmod=constants.kmod1*kmod2
        Fcd=kmod*(material.GetFck()/constants.securityCoefficient)
        Ncd=load*constants.securityCoefficient

        profileArea=((Ncd)/Fcd)*constants.kmod1
        xDimention=math.sqrt(profileArea/2)

        rotationRadius=(math.sqrt(((xDimention*2)*(xDimention**3))/profileArea)) #usei a menor direção pq a inercia é indiretamente proporcional ao kc. Logo a menor direçao gera o menor Kc

        slenderness = constants.bucklingLength/rotationRadius 
        relativeSlenderness = (slenderness*3.14)*math.sqrt(material.GetFck()/material.GetEcm()) 

        if relativeSlenderness>0.3:
            k=0.5*(1+0.2*(relativeSlenderness-0.3)+relativeSlenderness**2)
        
            kc= 1/(k+math.sqrt(k**2-relativeSlenderness**2))

            profileArea=Ncd/Fcd*kc

        if profileArea<0.005:
            profileArea=0.005

        xDimention=math.sqrt(profileArea/2)
        

        return xDimention


def GetYDimention(load, material):

        if material.GetRelativeHumidity() <= 0.65:
            kmod2 = 1.0
        elif material.GetRelativeHumidity() > 0.65 and material.GetRelativeHumidity() <= 0.75:
            kmod2 = 0.9
        elif material.GetRelativeHumidity() > 0.75 and material.GetRelativeHumidity() <= 0.85:
            kmod2 = 0.8
        elif material.GetRelativeHumidity() > 0.75:
            kmod2 = 0.7

        kmod=constants.kmod1*kmod2
        Fcd=kmod*(material.GetFck()/constants.securityCoefficient)
        Ncd=load*constants.securityCoefficient

        profileArea=((Ncd)/Fcd)*constants.kmod1
        xDimention=math.sqrt(profileArea/2)

        rotationRadius=(math.sqrt(((xDimention*2)*(xDimention**3))/profileArea)) #usei a menor direção pq a inercia é indiretamente proporcional ao kc. Logo a menor direçao gera o menor Kc

        slenderness = constants.bucklingLength/rotationRadius 
        relativeSlenderness = (slenderness*3.14)*math.sqrt(material.GetFck()/material.GetEcm()) 

        if relativeSlenderness>0.3:
            k=0.5*(1+0.2*(relativeSlenderness-0.3)+relativeSlenderness**2)
        
            kc= 1/(k+math.sqrt(k**2-relativeSlenderness**2))

            profileArea=Ncd/Fcd*kc

        if profileArea<=0.005:
            profileArea=0.005

        xDimention=math.sqrt(profileArea/2)
        yDimention=xDimention/2

        return yDimention