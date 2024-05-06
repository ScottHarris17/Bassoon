# -*- coding: utf-8 -*-
"""
Created on Sat May  4 00:58:21 2024

Grating moves across the screen as an overlaid scotoma mask changes density

@author: mrsco
"""
from protocols.protocol import protocol
from psychopy import core, visual, data, event, monitors
import serial, random, math
import numpy as np

class ScotomaMovingGrating(protocol):
    def __init__(self):
        super().__init__()
        self.protocolName = 'ScotomaMovingGrating'
        
        #grating parameters
        self.gratingColor = [1.0, 1.0, 1.0]
        self.gratingContrast = 1.0 #multiplied by the color
        self.meanIntensity = 0.0; #mean intensity of the grating
        self.spatialFrequency = 0.1 #cycles per degree
        self.gratingTexture = 'sin' #can be 'sin', 'sqr', 'saw', 'tri', None
        self.speed = 10.0 #deg/s
        self.orientations = [90]#[float(x*45) for x in range(8)] #list of floats - degrees
        self.backgroundColor = [0.0, 0.0, 0.0]
        
        #scotoma parameters
        self.scotomaStartFraction = 0.2 #Fraction of pixels that start as a scotoma
        self.scotomaEndFraction = 1.0 #fraction of pixels that end as a scotoma
        self.scotomaOpacity = 1.0 #1 is fully opaque, 0 is fully transparent
        self.scotomaReverse = True #bool, True means that the scotoma will go from start to end and then end to start, False means it will only go from start to end
        self.scotomaGrowthTime = 20.0 #amount of time that the stimulus grows for
        self.scotomaBookendTime = 3.0 #seconds before scotoma comes online, while the grating is still moving. Also the amount of time to pause for in a reversal stimulus, and the amount of time that the grating continues to move for after the stimulus has gone away.
        self.scotomaGrowth = 'lin' #currently only 'lin' is supported for linear growth
        self.scotomaSize = 0.1 #in degrees. Scotomas will be square, such that height == width
        
        self.stimulusReps = 3        
        self.preTime = 1.0 #s
        self.stimTime = 0.0 #the total time that the grating moves for. This number is calculated during run time and should not be edited here. It is listed here as a dummy variable because it is required by the getFR method in protocol.py
        self.tailTime = 1.0 #s
        self.interStimulusInterval = 1.0 #s - wait time between each stimulus. backGround color is displayed during this time
        self._angleOffset = 0.0 # reassigned by the experiment in most cases


    def internalValidation(self, tf = True, errorMessage = ''):
        '''
        Validates the properties. This is called when the user updates the protocol's properties. It is directly called by the validatePropertyValues() method in the protocol super class
    
        -------
        Returns:
            tf - bool value, true if validations are passed, false if they are not
            errorMessage - string, message to be displayed in validations are not passed
    
        '''
        if self.scotomaStartFraction > 1 or self.scotomaStartFraction < 0 or self.scotomaEndFraction > 1 or self.scotomaEndFraction < 0:
            tf = False
            errorMessage = 'The scotoma start and end fractions must be a value between 0 and 1. If set to 1, all pixels will be blanked. If set to 0, no pixels will be blanked. If set to 0.5, half of the pixels will be blanked.'
        
        elif self.scotomaGrowth != 'lin':
            tf = False
            errorMessage = 'The Scotoma Growth parameter must be set to "lin". Other growth options will be supported in future versions.'
        
        elif self.scotomaOpacity > 1 or self.scotomaOpacity < 0:
            tf = False
            errorMessage = 'Scotoma Opacity must be between 0.0 and 1.0. 1 is fully opaque, 0 is transparent.'
            
        if self.stimTime != 0:
            self.stimTime = 0
            print('\nNOTE: Stim Time was reset to 0. It will be updated during run time. Users should not manually change this parameter for the Scotoma Moving Grating stimulus')
            
        if self.scotomaSize < 0.5:
            print('\nNOTE: Scotoma Size is small. This may slow down the frame rate. If this occurs, increase scotoma size to improve the frame rate')
            
        return tf, errorMessage


    def estimateTime(self):
        '''
        Estimate the total amount of time that this protocol will take to run
        given the current parameters

        Value is stored as total time in seconds in the property 'self._estimatedTime'
        which is initialized by the protocol superclass.

        returns: estimated time in seconds
        '''
        if self.scotomaReverse:
            st = 3*self.scotomaBookendTime + 2*self.scotomaGrowthTime
        else:
            st = 2*self.scotomaBookendTime + self.scotomaGrowthTime
            
        timePerEpoch = self.preTime + st + self.tailTime + self.interStimulusInterval
        numberOfEpochs = self.stimulusReps * len(self.orientations)
        self._estimatedTime = timePerEpoch * numberOfEpochs #return estimated time for the total stimulus in seconds

        return self._estimatedTime


    def createOrientationLog(self):
        '''
        Generate a random sequence of orientations given the desired orientations

        Desired orientations are specified as a list in self.orientations

        creates self._orientationLog, a list, which specifies the orienation
        to use for each epoch
        '''
        orientations = self.orientations
        self._orientationLog = []
        random.seed(self.randomSeed) #reinitialize the random seed

        for n in range(self.stimulusReps):
            self._orientationLog += random.sample(orientations, len(orientations))
            
    
    
    def createScotomaGrowthSequence(self, numScotomasToAdd, numTotalScotomas, scotomaIndices):
        '''
        Builds a sequence of scotoma indices to add or remove from the mask
        
        Inputs:
            - numScotomasToAdd: the total number of scotomas you need to add by the end of the growth sequence. Can be a positive or negative integer. If this number is negative, you'll be taking away scotomas from the mask rather than adding them
            - scotomaIndices: list 1d indices where scotomas have already been filled
            
        Returns:
            - no explicit returns, but creates variables self._newScotomasPerFrame (number of new scotomas to add on each frame) and self._scotomaSequence (list of indices that indicate where to add or take away scotomas in sequence)
        '''
        
        if self.scotomaGrowth == 'lin':
            #First figure out an integer number of scotomas to add on each frame. Consider that you need to add an integer number on each frame, and the frame rate may not divide the growth rate evenly
            meanScotomasAddedPerFrame = numScotomasToAdd / self._numFramesGrowth
            cumulativeScotomasAdded = np.round(np.cumsum([meanScotomasAddedPerFrame for f in range(self._numFramesGrowth)]))
            self._newScotomasPerFrame = np.diff(cumulativeScotomasAdded) #new scotomas per frame is the number of new additions to make on every sequential frame.
            self._newScotomasPerFrame = [int(el) for el in self._newScotomasPerFrame] #convert to list of integers
            self._newScotomasPerFrame = [round(meanScotomasAddedPerFrame)] + self._newScotomasPerFrame
            
        elif self.scotomaGrowth == 'exp':
            #   --- enter code here for exponential growth pattern --- #
            pass
            
        #if adding scotomas:
        if numScotomasToAdd > 0:
            noScotomaIndices = list(set([i for i in range(numTotalScotomas)]) - set(scotomaIndices))
            self._scotomaSequence = np.array(random.sample(noScotomaIndices, numScotomasToAdd)) 

        #if subtracting scotomas:
        if numScotomasToAdd < 0:
            self._scotomaSequence = np.array(random.sample(scotomaIndices, -numScotomasToAdd))
            self._newScotomasPerFrame = [-x for x in self._newScotomasPerFrame]
            
    
    def run(self, win, informationWin):
        '''
        Executes the ScotomaMovingGrating stimulus
        '''
        
        self._completed = 0 #started but not completed

        self._informationWin = informationWin #tuple, save here so you don't have to pass this as a function parameter every time you use it
        
        #update the stim time
        if self.scotomaReverse:
            self.stimTime = 3*self.scotomaBookendTime + 2*self.scotomaGrowthTime
        else:
            self.stimTime = 2*self.scotomaBookendTime + self.scotomaGrowthTime
            
        self.getFR(win)
        self._interStimulusIntervalNumFrames = round(self._FR * self.interStimulusInterval)
        self._actualInterStimulusInterval = self._interStimulusIntervalNumFrames * 1/self._FR

        stimMonitor = win.monitor
        pixPerDeg = self.getPixPerDeg(stimMonitor)

        #Pause for keystroke if the user wants to manually initiate
        if self.userInitiated:
            self.showInformationText(win, 'Stimulus Information: Scotoma Moving Grating\nPress any key to begin')
            event.waitKeys() #wait for key press

        spatialFrequencyCyclesPerPixel = self.spatialFrequency * (1/pixPerDeg)

        grating = visual.GratingStim(
            win,
            size = (win.size[0]*2, win.size[1]*2),
            sf = (spatialFrequencyCyclesPerPixel, None),
            tex = self.gratingTexture,
            contrast = self.gratingContrast,
            color = self.gratingColor,
            )
        
        #create the mask
        winWidthPix = win.size[0]
        winHeightPix = win.size[1]

        scotomaSizePix = int(self.scotomaSize*pixPerDeg) #maybe a slight rounding error here by using int
        
        #specify the x and y center coordinates for each check
        xCoordinates = [x - win.size[0]/2 for x in range(-scotomaSizePix, win.size[0]+scotomaSizePix, scotomaSizePix)]
        yCoordinates = [y - win.size[1]/2 for y in range(-scotomaSizePix, win.size[1]+scotomaSizePix, scotomaSizePix)]
        numTotalScotomas = len(xCoordinates) * len(yCoordinates)
        sizes = [(scotomaSizePix, scotomaSizePix) for i in range(numTotalScotomas)]
       
        self._scotomaCoordinates = []
        colors = []
        for i in range(len(xCoordinates)):
            for j in range(len(yCoordinates)):
                self._scotomaCoordinates.append([xCoordinates[i], yCoordinates[j]])
                
        scotomaMask = visual.ElementArrayStim(
            win,
            nElements = numTotalScotomas,
            elementMask="None",
            elementTex = None,
            xys = self._scotomaCoordinates,
            sizes = sizes,
            colors = self.backgroundColor
            )
        
        random.seed(self.randomSeed) #reinitialize the random seed
        
        mask = np.zeros((numTotalScotomas, 1)) #1 is fully transparent, -1 is fully opaque. Start with a fully transparent mask.
    
        #fill the mask with the number of scotomas needed at the start of the stimulus
        numScotomasStart = round(numTotalScotomas*self.scotomaStartFraction)
        scotomaIndices = random.sample([i for i in range(numTotalScotomas)], numScotomasStart)
        mask[scotomaIndices] = self.scotomaOpacity
            
        scotomaMask.opacities = mask #set the first mask
        
        
        #Now build up a list of which mask locations you want to update on each frame 
        numScotomasEnd = round(numTotalScotomas*self.scotomaEndFraction)
        numScotomasToAdd = numScotomasEnd - numScotomasStart #note, this value can be positive or negative.
            
        self._numFramesGrowth = round(self._FR * self.scotomaGrowthTime) #number of frames overwhich the scotoma will grow
        self._actualScotomaGrowthTime = self._numFramesGrowth * 1/self._FR
        
        self._numFramesBookend = round(self._FR * self.scotomaBookendTime)
        self._actualBookendTime = self._numFramesBookend * 1/self._FR
        
        #create self._scotomaSequence and self._newScotomasPerFrame
        self.createScotomaGrowthSequence(numScotomasToAdd, numTotalScotomas, scotomaIndices)
            
        #create flipped copies of self._scotomaSequence and self._newScotomasPerFrame if you will also be doing a reversel
        if self.scotomaReverse:
            scotomaSequenceReverse = np.flip(self._scotomaSequence)
            newScotomasPerFrameReverse = np.flip(self._newScotomasPerFrame)
        
        #The cover rectangle is drawn on top of the primary grating. It is used
        #to change the mean intensity of the grating when the user desires.
        #If the mean intensity is set to 0, then the cover rectangle is still
        #drawn but with an opacity of 0
        coverRectangle = visual.Rect(
            win,
            size = (win.size[0]*2, win.size[1]*2),
            opacity = 0
            )

        if self.meanIntensity > 0:
            coverRectangle.fillColor = [1, 1, 1]
            coverRectangle.opacity = self.meanIntensity
        elif self.meanIntensity < 0:
            coverRectangle.fillColor = [-1, -1, -1]
            coverRectangle.opacity = -1*self.meanIntensity

        self._numCyclesToShiftByFrame = self.speed*self.spatialFrequency*(1/self._FR)

        self.createOrientationLog()
        
        
        totalEpochs = len(self._orientationLog)
        epochNum = 0
        trialClock = core.Clock() #this will reset every trial
                
        #stimulus loop
        for ori in self._orientationLog:
            grating.ori = -ori - self._angleOffset #flip for coordinate convention: 0 = east, 90 = north, 180 = west, 270 = south
            epochNum += 1
            #show information if necessary
            if self._informationWin[0]:
                self.showInformationText(win, 'Running Scotoma Moving Grating. Current orientation = ' + \
                                         str(ori) + '\n Epoch ' + str(epochNum) + ' of ' + str(totalEpochs))


            #pause for inter stimulus interval
            win.color = self.backgroundColor
            for f in range(self._interStimulusIntervalNumFrames):
                win.flip()
                if self.checkQuitOrPause():
                    return

            #pretime... stationary grating
            self._stimulusStartLog.append(trialClock.getTime())
            self.sendTTL()
            self._numberOfEpochsStarted += 1
            for f in range(self._preTimeNumFrames):
                grating.draw()
                coverRectangle.draw()
                scotomaMask.draw()
                win.flip()
                if self.checkQuitOrPause():
                    return

            
            #stim time
            
            #bookend 1 (grating starts moving before stimulus moves)
            for f in range(self._numFramesBookend):
                grating.phase += self._numCyclesToShiftByFrame
                grating.draw()
                coverRectangle.draw()
                scotomaMask.draw()
                win.flip()
                if self.checkQuitOrPause():
                    return
            
            #first check whether you will be adding or taking away scotomas. Assign the addColor accordingly so that when you update the mask it either places a scotoma or sets the value to transparent
            if numScotomasToAdd > 0:
                addColor = self.scotomaOpacity #scotoma color, used when adding scotomas
            else:
                addColor = 0 #transparent - used when taking away scotomas
                
            count = 0 
            for f in range(self._numFramesGrowth):
                scotomasToChangeThisFrame = self._scotomaSequence[count:count+self._newScotomasPerFrame[f]]
                count += self._newScotomasPerFrame[f]
                mask[scotomasToChangeThisFrame] = addColor
                scotomaMask.opacities = mask
                grating.phase += self._numCyclesToShiftByFrame
                grating.draw()
                coverRectangle.draw()
                scotomaMask.draw()
                win.flip()
                if self.checkQuitOrPause():
                    return
            
            #middle bookend
            if self.scotomaReverse:
                #pause time before reversal
                for f in range(self._numFramesBookend):
                    grating.phase += self._numCyclesToShiftByFrame
                    grating.draw()
                    coverRectangle.draw()
                    scotomaMask.draw()
                    win.flip()
                    if self.checkQuitOrPause():
                        return
                
                if numScotomasToAdd > 0:
                    addColor = 0 #if you were originally adding scotomas, now you'll take them away
                else:
                    addColor = self.scotomaOpacity #if you were originally taking away scotomas, now you'll add them
                #flip the scotoma sequence and scotomas to change this frame lists
                count = 0
                for f in range(self._numFramesGrowth):
                    scotomasToChangeThisFrame = scotomaSequenceReverse[count:count+newScotomasPerFrameReverse[f]]
                    count += newScotomasPerFrameReverse[f]
                    mask[scotomasToChangeThisFrame] = addColor
                    scotomaMask.opacities = mask
                    grating.phase += self._numCyclesToShiftByFrame
                    grating.draw()
                    coverRectangle.draw()
                    scotomaMask.draw()
                    win.flip()
                    if self.checkQuitOrPause():
                        return
                    
            #bookend 2
            for f in range(self._numFramesBookend):
                grating.phase += self._numCyclesToShiftByFrame
                grating.draw()
                coverRectangle.draw()
                scotomaMask.draw()
                win.flip()
                if self.checkQuitOrPause():
                    return

            #tail time
            for f in range(self._tailTimeNumFrames):
                grating.draw()
                coverRectangle.draw()
                scotomaMask.draw()
                win.flip()
                if self.checkQuitOrPause():
                    return


            self._stimulusEndLog.append(trialClock.getTime())
            self.sendTTL()
            win.flip();win.flip() #two flips to allow for a pause for TTL writing

            self._numberOfEpochsCompleted += 1


        self._completed = 1
