# helper class to load MetaImage information from a file
#
# Copyright (C) 2008  'Peter Roesch' <Peter.Roesch@fh-augsburg.de>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
# or open http://www.fsf.org/licensing/licenses/gpl.html

from __future__ import print_function, division

import sys
import os.path
import numpy
import numpy as np
from PIL import Image
#import matplotlib.pyplot as plt
import scipy.misc
import viz
import vizact
import vizshape
import vizinfo
import os
import shutil
import vizconnect

class MetaImage (object):
    '''Load 3D image characteristics from a mhd file
    '''
    def __init__(self, fileName, doDataLoad=True):
        self.__dataTypeMap = \
                {'MET_UCHAR': numpy.uint8, 'MET_CHAR': numpy.int8,
                 'MET_USHORT': numpy.uint16, 'MET_SHORT': numpy.int16,
                 'MET_UINT': numpy.uint32, 'MET_INT': numpy.int32,
                 'MET_ULONG': numpy.uint64, 'MET_LONG': numpy.int64,
                 'MET_FLOAT': numpy.float32, 'MET_DOUBLE': numpy.float64}
        self.__dic = {}
        self.__loadMHD(fileName)
        self.NDims = 3
        if 'NDims' in self.__dic:
            self.NDims = int(self.__dic['NDims'][0])
        self.BinaryDataByteOrderMSB = []
        if 'BinaryDataByteOrderMSB' in self.__dic:
            self.BinaryDataByteOrderMSB \
                = bool(self.__dic['BinaryDataByteOrderMSB'][0])
        self.TransformMatrix = [1, 0, 0, 0, 1, 0, 0, 0, 1]
        if 'TransformMatrix' in self.__dic:
            self.__readPar('TransformMatrix', self.TransformMatrix,
                           float, '0', 9)
        self.Offset = []
        self.__readPar('Offset', self.Offset, float, '0', self.NDims)
        self.CenterOfRotation = []
        self.__readPar('CenterOfRotation', self.CenterOfRotation,
                       float, '0', self.NDims)
        self.ElementSpacing = []
        self.__readPar('ElementSpacing', self.ElementSpacing,
                       float, '0', self.NDims)
        self.DimSize = []
        self.__readPar('DimSize', self.DimSize, int, '1', self.NDims)
        self.ElementType = None
        if 'ElementType' in self.__dic:
            self.ElementType = self.__dic['ElementType'][0]
            if self.ElementType in self.__dataTypeMap:
                self.__numpyDataType = self.__dataTypeMap[self.ElementType]
            else:
                print('illegal data type ', self.ElementType)
                sys.exit()
        self.ElementDataFile = None
        if 'ElementDataFile' in self.__dic:
            self.ElementDataFile = self.__dic['ElementDataFile'][0]
        self.dataArray = None
        if doDataLoad:
            self.__loadData(os.path.join(
                os.path.dirname(fileName), self.ElementDataFile))

    def __readPar(self, name, target, type, defaultValue, dim=3):
        for i in range(dim):
            if name in self.__dic:
                target.append(type(self.__dic[name][i]))
            else:
                target.append(type(defaultValue))

    def __loadMHD(self, fileName):
        try:
            mhdFile = open(fileName, 'r')
        except FileNotFoundError:
            print('could not open file ', fileName)
            sys.exit()
        for line in mhdFile:
            words = line.split()
            if len(words) > 0:
                self.__dic[words[0]] = words[2:]
        mhdFile.close()

    def __loadData(self, fName):
        try:
            dataFile = open(fName, 'r')
        except FileNotFoundError:
            print('could not open file ', self.ElementDataFile)
            sys.exit()
        size = 1
        for i in range(self.NDims):
            size = size * self.DimSize[i]
        tmpArray = numpy.fromfile(dataFile, self.__numpyDataType)
        self.dataArray = tmpArray.reshape(self.DimSize[::-1])
        dataFile.close()

#TestEvent, nothing more
class QuadColorChanger(viz.EventClass):
    def __init__(self):
        #Call super class constructor
        viz.EventClass.__init__(self)

        #Setup event count displayer
        self.__eventCount = 0
        self.__countDisplay = viz.addText( '0', parent=viz.ORTHO, fontSize=40, pos=(10,10,0) )

    def incMeter(self, quad):
        #Increment and display event counter
        self.__eventCount += 1
        self.__countDisplay.message( str(self.__eventCount) )


if __name__ == '__main__':
    """if len(sys.argv) != 2:
        print('usage: python MetaImage.py mhdFileName')
        sys.exit(0) """
    filename = "Carp.mhd"
    #image = MetaImage(sys.argv[1], doDataLoad=True) -> original
    image = MetaImage(filename, doDataLoad=True)
    print('image DimSize: ', image.DimSize)
    print('image Offset:  ', image.Offset)
    print('image TransformMatrix:  ', image.TransformMatrix)
    print('image ElementSpacing: ', image.ElementSpacing)
    print('average grey value: ', image.dataArray.mean())
    print('grey value standard deviation: ', image.dataArray.std())
    print(image.dataArray)
    
    #print 2d image with numpy array data
    print("\nArray Data: ", image.ElementSpacing)
    print(type(image.dataArray))
    img = Image.fromarray(image.dataArray, "RGB")
    print ("Shape: ", image.dataArray.shape)
    testSlice = image.dataArray[:, 180,:]
    print("Test", testSlice)
    testSliceImage = Image.fromarray(testSlice, "L")
    #testSliceImage.show()
    testSliceImage.save("Texture.png")
    #img.show()
    img.save('my.png')
    # Original: x = np.array([(0.78125, 0.390625, 1.0)])
    x = np.array([(0.78125, 0.390625, 1.0)])
    print(x)
    img2 = Image.fromarray(x)
    #img2.show()
    img.save("test3.png")
    
    ### convert to uint8 / 255 grey
    testSliceConvert = image.dataArray[:, 0,:] #-> second number, from 0 to 255, all slices
    print(type(testSliceConvert))
    testSliceConvert = testSliceConvert.astype(np.uint8)
    print("Test ConvertImage", testSlice)
    testSliceImage = Image.fromarray(testSliceConvert, "L")
    testSliceImage.show()
    testSliceImage.save("TextureConvert.png")
    
    """
    ### Test: iterate all images from 0 to 255
    n = 0
    while n != 256:
        testSliceConvert = image.dataArray[:, n,:] #-> second number, from 0 to 255, all slices
        testSliceConvert = testSliceConvert.astype(np.uint8)
        testSliceImage = Image.fromarray(testSliceConvert, "L")
        ImageFileName = "TextureConventNumber" + str(n) + ".png"
        print(ImageFileName)
        testSliceImage.save(ImageFileName)
        print("Created Slice Number ", n)
        n = n+1
    print("done")
    """
    
    viz.setMultiSample(4)
    viz.fov(60)
    viz.go()
    
    vizconnect.go(r'oculus_control.py')

    viz.addChild('ground_gray.osgb')
    
    #Add slider in info box
    #Initialize info box with some instructions
    info = vizinfo.InfoPanel('Use slider to change the slices of the carp', align=viz.ALIGN_RIGHT_TOP, icon=False)
    info.setTitle( 'Slice Changer' )
    info.addSeparator()
    slider = info.addLabelItem('Slice Number', viz.addSlider())
    slider.label.color(viz.RED)

    quad = viz.addTexQuad(size = [1, 2]) 

    def testEvent(key): 
    #Do something with 'key' variable 
        pass

    #with movement to the back (scripted, not real)
    def ChangeSliceTexture(sliceNumber):
        TextureName = "textures/TextureConventNumber" + str(sliceNumber) + ".png"

        #default number = 3.0
        movementNumber = 3.0
        # default multiplicator
        multiNumber = 0.003921
        newMovementNumber = movementNumber + (multiNumber * sliceNumber)
        pic = viz.addTexture(TextureName) 
        quad.setPosition([-.75, 2, newMovementNumber]) #put quad in view
        quad.texture(pic)

    #create the necessary texture, but still saved it
    def CreateTextureOnTheFly(textureNumber):
        
        # create folder "textures
        newpath = 'textures' 
        if os.path.exists(newpath):
            shutil.rmtree(r'textures')
        if not os.path.exists(newpath):
            os.makedirs(newpath)
        
        testSliceConvert = image.dataArray[:, textureNumber,:] #-> second number, from 0 to 255, all slices
        testSliceConvert = testSliceConvert.astype(np.uint8)
        testSliceImage = Image.fromarray(testSliceConvert, "L")
        ImageFileName = "textures/TextureConventNumber" + str(textureNumber) + ".png"
        print(ImageFileName)
        testSliceImage.save(ImageFileName)
        print("Created Slice Number ", textureNumber)
        
        ###test: image size
        im = Image.open(ImageFileName)
        width, height = im.size
        print(width)
        print(height)
        ###test done

    def SetSliceNumber(pos):
        #Make wheelbarrow spin according to slider position
        #wheelbarrow.runAction( vizact.spin(0, -1, 0, 500 * pos) )
        sliceNumber = pos * 255
        print(int(round(sliceNumber)))
        CreateTextureOnTheFly(int(round(sliceNumber)))
        ChangeSliceTexture(int(round(sliceNumber)))
        return int(round(sliceNumber))

    ### experimental, maybe crap
    defaultNumber = 0
    numberOfTexture = SetSliceNumber(defaultNumber)
    TextureName = "TextureConventNumber" + str(numberOfTexture) + ".png"

    #Texture on 2d quad
    pic = viz.addTexture(TextureName) 
    #quad = viz.addTexQuad() 
    quad.setPosition([-.75, 2, 3]) #put quad in view 
    quad.texture(pic)

    """
    #Texture on 3d object
    t1 = viz.add('TextureConventNumber180.png')
    object3d = vizshape.addBox(size=(5.0,3.0,3.0), splitFaces=True,pos=(0,1.8,4))
    object3d.texture(t1,node='back')
    """

    vizact.onslider(slider, SetSliceNumber)
   
    ###########
    #test, maybe crap: controlls with laser pointer / touch
    
    #Animate shapes
    #quad.addAction(vizact.spin(0,-1,0,15))
    
    shapes = [quad]
    lp = vizconnect.getRawTool('highlighter')
    lp.setItems(shapes)
    grabber = vizconnect.getRawTool('grabber')
    grabber.setItems(shapes)
    
    
    def movePicture():
        #quad.setEuler,([vizact.elapsed(90),0,0],viz.REL_PARENT)
        print("geht wohl nicht")
    
    ############
    #rotation controlls for keyboard
    vizact.whilekeydown('a',quad.setEuler,[vizact.elapsed(90),0,0],viz.REL_PARENT)
    vizact.whilekeydown('d',quad.setEuler,[vizact.elapsed(-90),0,0],viz.REL_PARENT)
    vizact.whilekeydown('w',quad.setEuler,[0,vizact.elapsed(90),0],viz.REL_PARENT)
    vizact.whilekeydown('s',quad.setEuler,[0,vizact.elapsed(-90),0],viz.REL_PARENT)
    
    #rotation controlls for Touch, maybecrap
    def myFunction(e):
        print ("event triggered")
        quad.setEuler,[vizact.elapsed(90),0,0],viz.REL_PARENT

    viz.callback(viz.getEventID('touchControl'), myFunction) 