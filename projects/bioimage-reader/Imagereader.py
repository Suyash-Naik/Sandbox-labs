import numpy as np
from glob import glob
import os
import matplotlib.pyplot as plt
import pandas as pd
import tifffile as tiff

class ImageReader:
    """A class that reads a image>
    ----> Finds the pixels with non zeros  values
    ----> Finds the position of these pixels 
    ----> Finds the intensity of these pixels
    ----> Makes a PD with the position and intensity of the pixels"""
    def __init__(self,path):
        self.path = path
        self.imagepath = glob(path+"*3dann*")[0]
        self.image=tiff.imread(self.imagepath)
        self.frames = self.image.shape[0]
        self.height = self.image.shape[1]
        self.width = self.image.shape[2]
        self.pixel=input("Enter the pixel size in µm:")
        self.time=input("Enter the time interval in seconds:")

    def showimage(self,frame):
        plt.imshow(self.image[frame])
        plt.show()

    def darkpixel(self):
        pdDarkpixel = pd.DataFrame(columns=["PixelID",'Frame', 'X', 'Y', 'Intensity'])
        for i in range(self.frames):
            for j in range(self.height):
                for k in range(self.width):
                    if self.image[i,j,k] != 0:
                        pdDarkpixel = pdDarkpixel.append({'PixelID':str(i)+str(j)+str(k),'Frame':i, 'X':j, 'Y':k, 'Intensity':self.image[i,j,k]}, ignore_index=True)
        return pdDarkpixel
    
    
        