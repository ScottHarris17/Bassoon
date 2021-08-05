# -*- coding: utf-8 -*-
"""
Created on Wed Aug  4 13:10:16 2021

@author: mrsco
"""

def pixelsWide(pixelsMeasured, cordMeasured, domeRadius = 30.48, screenWidth = 100, eyeDistance = 100):
    '''
    This function will tell you how to set up a psychopy monitor given certain measurements about the dome
    Procedure, using the morph file that you plan to use in an experiment, project an image of known
    size in pixels onto the dome. For example, a bar of known width in pixels. Then measure the length of 
    the cord that connects two points of known distance in your projected image (e.g. the cord that connects two sides of the dome).
    
    The number of pixels of the projected image is the 'pixelsMeasured' input and the measured size (in cm) is the 'cordMeasured' input.
    
    domeRadius is the radius of the dome in cm.
    
    screenWidth and eyeDistance can be arbitrary numbers. Their default is set to 100 for ease. I wouldn't recommend changing them
    
    The function will print the measurements that you have to asign to the psychopy monitor
    
    The output of the function is the pixelsWide value that you'll asign to the psychopy monitor. This is the only 
    monitor value that is actually calculated since it is a function of the other three.
    '''
    
    import math  
    pixelsWide = (pixelsMeasured*math.degrees(math.atan((screenWidth/2)/eyeDistance)))/(math.degrees(math.asin((cordMeasured/2)/domeRadius)))
    totalDegrees = 2*math.degrees(math.atan((screenWidth/2)/eyeDistance))
    pixelsPerDegree = pixelsWide/totalDegrees
    print('Set monitor to:\nWidth (cm) =', screenWidth, '\nEye Distance (cm) =', eyeDistance, '\nHorizontal Pixels =', pixelsWide, )
    print('Pixels Per Degree will be:', pixelsPerDegree) #prints pixels per visual degree as a reference. Make sure this is what you expect it to be
    return pixelsWide


#20210805 
pixMeasured = 140
cordCM = 24.765
horizPix = pixelsWide(pixMeasured, cordCM)


#set the monitor
from psychopy.monitors import Monitor
m = Monitor('projector_405')
m.setSizePix([horizPix, 100])
m.setDistance(100)
m.setWidth(100)
m.save()