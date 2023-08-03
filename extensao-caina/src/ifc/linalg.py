# -*- coding: utf-8 -*-
import numpy as np

# TODO: Add more funcionalities

class Transform:
    def __init__(self, pos=np.array([0.0, 0.0, 0.0]), rot=np.array([0.0, 0.0, 0.0])):
        self.__pos = pos
        self.__rot = np.radians(rot)
        self.__data = np.matmul(self.__Translate(), self.__Rotate())

    def GetPosition(self):
        return self.__pos
    
    def GetRotation(self):
        return self.__rot

    def GetData(self):
        return self.__data

    def __Translate(self):
        mat = np.array([[1, 0, 0, self.__pos[0]],
                        [0, 1, 0, self.__pos[1]],
                        [0, 0, 1, self.__pos[2]],
                        [0, 0, 0, 1]])
        return mat

    def __Rotate(self):
        rotX = np.array([[1, 0, 0, 0],
                         [0, np.cos(self.__rot[0]), -np.sin(self.__rot[0]), 0],
                         [0, np.sin(self.__rot[0]),  np.cos(self.__rot[0]), 0],
                         [0, 0, 0, 1]])
        
        rotY = np.array([[ np.cos(self.__rot[1]), 0, np.sin(self.__rot[1]), 0],
                         [0, 1, 0, 0],
                         [-np.sin(self.__rot[1]), 0, np.cos(self.__rot[1]), 0],
                         [0, 0, 0, 1]])

        rotZ = np.array([[np.cos(self.__rot[2]), -np.sin(self.__rot[2]), 0, 0],
                         [np.sin(self.__rot[2]),  np.cos(self.__rot[2]), 0, 0],
                         [0, 0, 1, 0],
                         [0, 0, 0, 1]])

        return np.matmul(rotZ, np.matmul(rotY, rotX))