# -*- coding: utf-8 -*-
"""
Created on Tue Oct 31 11:59:13 2023
 
ImageJitter

Uses natural images from van Hateren database. Images are jittered randomly in 
x and y.

Must use .jpg images only.

@author: mrsco
"""


from protocols.protocol import protocol
from psychopy import core, visual, data, event, monitors
import serial, random, math
import os, glob, json
import numpy as np


class ImageJitter(protocol):
    def __init__(self):
        super().__init__()
        self.protocolName = 'ImageJitter'
        self.speedStandardDeviation = 100.0 #deg/s
        self.recenterSpeed = 10.0 #deg/s - used to recenter the image if it drifts off too far
        self.backgroundColor = [0.0, 0.0, 0.0]
        self.stimulusReps = 3
        self.preTime = 1.0 #s
        self.stimTime = 60.0 #s
        self.tailTime = 1.0 #s
        self.interStimulusInterval = 3.0 #s - wait time between each stimulus. backGround color is displayed during this time
        self._angleOffset = 0.0 # reassigned by the experiment in most cases
        self.apertureDiameter = 20.0 #degrees
        self.imageStartingPosition = [0.0, 0.0] #x, y deg
        self.moveMeanFrames = 100 #number of frames to do the moving mean over for the stimulus speed
        
        #guess the file directory
        scriptDir = os.path.dirname(__file__)
        bassoonIndex = scriptDir.rfind('Bassoon')
        pathThroughBassoon = scriptDir[:bassoonIndex+len("Bassoon")]
        pathToImagesFromBassoon = 'src/images/stimulusImages/example'
        
        self.imageFileExtension = '*.jpg' #string can use glob.glob style pattern matching
        self.imageFolderPath = os.path.join(pathThroughBassoon, pathToImagesFromBassoon) #string can include glob style pattern matching
                
        
    def estimateTime(self):
        '''
        Estimate the total amount of time that this protocol will take to run
        given the current parameters

        Value is stored as total time in seconds in the property 'self.estimatedTime'
        which is initialized by the protocol superclass.

        returns: estimated time in seconds
        '''
        timePerEpoch = self.preTime + self.stimTime + self.tailTime + self.interStimulusInterval
        self._estimatedTime = timePerEpoch * self.stimulusReps #return estimated time for the total stimulus in seconds
        
        return self._estimatedTime
    
    
    def findImageInfo(self):
        '''
        Finds the available image files given the path and file type specified in the attributes
        
        Returns: imagesFound, bool value.
        '''
        imagesFound = False
        
        fullGlobPath = os.path.join(self.imageFolderPath, self.imageFileExtension)
        self._allImgs = glob.glob(fullGlobPath)
        
        if len(self._allImgs) == 0:
            print('!!! WARNING: No images were found at the given file location')
            return
        
        #extract the image data in the JSON file that is located in the image folder
        #look for JSON file
        jsons = glob.glob(os.path.join(self.imageFolderPath, '*.json'))
        
        #load the JSON file
        with open(jsons[0]) as f:
            try:
                data = json.load(f)
                #stimWindow
                self._imageHeight_Pix = data['ImageHeight_Pix']
                self._imageWidth_Pix = data['ImageWidth_Pix']
                self._pixPerDeg_RawImages = data['ImagePixPerDeg']
            except:
                print("!!! JSON Data is Missing or Incorrect for these images, loading default values from UPENN natural image dataset.")
                self._imageHeight_Pix = 2000
                self._imageWidth_Pix = 3008
                self._pixPerDeg_RawImages = 92.0
        
        imagesFound = True
        return imagesFound
        
    
    
    def createImageSequence(self):
        '''
        Creates self._imageSequence, a list of paths to load the image objects 
        to. The length of the list is equal to self.stimulusReps.
        
        If stimulus reps is greater than the number of available images, then images will be repeated
        '''
        random.seed(self.randomSeed) #reinitialize the random seed
        timesLarger = math.ceil(self.stimulusReps/len(self._allImgs)) #handles if stimulusReps is bigger than total number of Images
        sequence = []
        remaining = self.stimulusReps - 0 #hacky way to get a new pointer
        for i in range(timesLarger):
            if remaining > len(self._allImgs):
                numToAdd = len(self._allImgs)
            else:
                numToAdd = remaining - 0 #new pointer again
            
            sequence += random.sample(self._allImgs, numToAdd)
            remaining -= numToAdd
            
        self._imageSequence = [os.path.join(self.imageFolderPath, img) for img in sequence]

    
    
    def createPositionLog(self, pixPerDeg):
        '''
        Creates an nx2xm numpy array.
         - Dimension 1: n = number of frames per stimulus rep (i.e., equal to self._stimTimeNumFrames)
         - Dimension 2: x and y values for position of the image stimulus on the frame
         - Dimension 3: m = number of stimulus reps
         
         The values of the array correspond to the x,y position of the stimulus
         at frame n, on stimulus repetition m. Values are in PIXELS. To convert
         to visual degrees, multiply by self._pixPerDeg in analysis
        '''
        print('Generating the motion patterns for Image Jitter. This may take a while...')
        
        random.seed(self.randomSeed) #reinitialize the random seed
                
        self._positionLog_Pix = np.zeros([self._stimTimeNumFrames, 2, self.stimulusReps])
        
        apertureDiameterPix = self.apertureDiameter * pixPerDeg
        
        stdSpeedPix = self.speedStandardDeviation * pixPerDeg / self._FR
        
        recenterSpeedPix = self.recenterSpeed * pixPerDeg / self._FR
        componentRecenterPix = recenterSpeedPix/math.sqrt(2) #this may need changing, not sure
        
        for m in range(self.stimulusReps):
            recenterNeeded = False
            recenterBegan = False
            
            currentX = self.imageStartingPosition[0] #x , y - the starting position should always be 0, 0, which is centered
            currentY = self.imageStartingPosition[1]
            
            thisRep = np.zeros([self._stimTimeNumFrames, 2])
            for n in range(self._stimTimeNumFrames):
                if not recenterNeeded:
         
                    dx = random.gauss(0, stdSpeedPix)
                    dy = random.gauss(0, stdSpeedPix)
                    
                    thisRep[n, 0] = currentX + dx
                    thisRep[n, 1] = currentY + dy
                    
                    currentX += dx
                    currentY += dy
                    
                    #check if a recentering is needed
                    if self._imageHeight_Pix - abs(currentY) < apertureDiameterPix//2.5 or abs(currentY) > self._imageHeight_Pix//2.5 \
                        or self._imageWidth_Pix - abs(currentX) < apertureDiameterPix//2.5 or abs(currentX) > self._imageWidth_Pix//2.5:
                            recenterNeeded = True
                
                else: #recentering is needed
                    if not recenterBegan:
                        xyRatio = currentX/currentY
                        dy = componentRecenterPix/math.sqrt(xyRatio**2 + 1)
                        dx = xyRatio * dy
                       
                        if currentX < 0:
                            dx = abs(dx)
                        else:
                            dx = -abs(dx)
                        
                        if currentY < 0:
                            dy = abs(dy)
                        else:
                            dy = -abs(dy)
                            
                        distancePerFrame = math.sqrt(dx**2 + dy**2)
                        distanceToGo = math.sqrt(currentX**2 + currentY**2)
                        framesToGo = round(distanceToGo/distancePerFrame);
                        recenterBegan = True
                    
                    thisRep[n, 0] = currentX + dx
                    thisRep[n, 1] = currentY + dy
                    
                    currentX += dx
                    currentY += dy
                    
                    framesToGo -= 1
                    if framesToGo < 1:
                        recenterBegan = False
                        recenterNeeded = False
            
            #use a convolution to get the moving average
            xConv = np.convolve(thisRep[:, 0], np.ones(self.moveMeanFrames)/self.moveMeanFrames, mode = 'same')
            yConv = np.convolve(thisRep[:, 1], np.ones(self.moveMeanFrames)/self.moveMeanFrames, mode = 'same')
            
            self._positionLog_Pix[:, 0, m] = xConv
            self._positionLog_Pix[:, 1, m] = yConv
        
        print("Done!")

        
    def run(self, win, informationWin):
        '''
        Executes the ImageJitter stimulus
        '''
        self._completed = 0 #started but not completed

        self._informationWin = informationWin #tuple, save here so you don't have to pass this as a function parameter every time you use it

        self.getFR(win)
        self._interStimulusIntervalNumFrames = round(self._FR * self.interStimulusInterval)
        self._actualInterStimulusInterval = self._interStimulusIntervalNumFrames * 1/self._FR
   
        stimMonitor = win.monitor
        pixPerDeg = self.getPixPerDeg(stimMonitor)
        self._pixPerDeg = self.getPixPerDeg(stimMonitor) #only included for this stimulus to help with analysis of the position log (which is in pixels). Rerunning the function to create an independent pointer
        
        imagesFound = self.findImageInfo() #loads the list of images to use in the experiment and grabs data about them, list in self._allImgs
        if not imagesFound:
            print("!!! There was a problem locating the images and/or JSON data in the ImageJitter stimulus at path " \
                  + self.imageFolderPath + "\n \n !!! The Image Jitter stimulus is being ABORTED")
            return
        
        self.createImageSequence() #creates the self._imageSequence
        self.createPositionLog(pixPerDeg) #creates the position log in PIXEL units, self._positionLog_Pix

        #Pause for keystroke if the user wants to manually initiate
        if self.userInitiated:
            self.showInformationText(win, 'Stimulus Information: Image Jitter\nPress any key to begin')
            event.waitKeys() #wait for key press
            
        
        startingPositionPix = [p*pixPerDeg for p in self.imageStartingPosition]
        
        image = visual.ImageStim(
            win,
            image = None,
            pos = startingPositionPix,
            )
        
        aperture = visual.Aperture(
            win,
            shape = 'circle',
            size= self.apertureDiameter * pixPerDeg,
            pos = startingPositionPix,
            )

        epochNum = 0
        trialClock = core.Clock() #this will reset every trial
        
        self.burstTTL(win) #burst to mark onset of the stimulus

        #stimulus loop
        for img in self._imageSequence:
            image.image = img
            image.pos = startingPositionPix
            
            epochNum += 1
            #show information if necessary
            if self._informationWin[0]:
                self.showInformationText(win, 'Running Image Jitter. Current Image = '\
                                         + '\n Epoch ' + str(epochNum) + ' of ' + str(self.stimulusReps))


            #pause for inter stimulus interval
            win.color = self.backgroundColor
            for f in range(self._interStimulusIntervalNumFrames):
                win.flip()
                if self.checkQuitOrPause():
                    return

            #pretime... stationary image
            self._stimulusStartLog.append(trialClock.getTime())
            self.sendTTL()
            self._numberOfEpochsStarted += 1
            for f in range(self._preTimeNumFrames):
                image.draw()
                #aperture.draw()
                win.flip()
                if self.checkQuitOrPause():
                    return
            
            if self.writeTTL == 'Pulse':
                self._portObj.baudrate = 1000000

            #stim time - flash
            for f in range(self._stimTimeNumFrames):
                
                image.pos = (self._positionLog_Pix[f, 0, epochNum-1], self._positionLog_Pix[f, 1, epochNum-1])
                image.draw()
                win.flip()
                
                self.sendTTL()
                    
                if self.checkQuitOrPause():
                    return
            
            #return baudrate to high value
            if self.writeTTL == 'Pulse':
                self._portObj.baudrate = 4000000

            #tail time
            for f in range(self._tailTimeNumFrames):
                image.draw()
                #aperture.draw()
                win.flip()
                if self.checkQuitOrPause():
                    return


            self._stimulusEndLog.append(trialClock.getTime())
            self.sendTTL()
            win.flip();win.flip() #two flips to allow for a pause for TTL writing

            self._numberOfEpochsCompleted += 1

        self._positionLog_Pix = self._positionLog_Pix.tolist() #convert to list for JSON dump saving
        self._completed = 1
        