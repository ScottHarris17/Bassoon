# -*- coding: utf-8 -*-
"""
Created on Mon Jul 12 16:17:29 2021

Grating moves across the screen in directions specified in orientations parameter.
Order is random.

@author: mrsco
"""
from protocols.protocol import protocol
from psychopy import core, visual, data, event, monitors
import serial, random, math
import numpy as np

class MovingGratingDirection(protocol):
    def __init__(self):
        super().__init__()
        self.protocolName = 'MovingGratingDirection' #In Moving Grating Direction a grating texture moves across the screen in several different orientations.
        self.gratingColor = [1.0, 1.0, 1.0] #color of the grating (in RGB).-1.0 equates to 0 and 1.0 equates to 255 for 8 bit colors.
        self.gratingContrast = 1.0 #Sets the contrast of the grating by multiplying by the the grating color.
        self.meanIntensity = 0.0 #The mean intensity of the grating. This value should be between -1 and 1.0, where 0.0 is "middle gray"
        self.spatialFrequency = 0.15 #cycles per degree - the spatial frequency of the grating.
        self.gratingTexture = 'sin' #The pattern of the grating. This can be 'sin', 'sqr', 'saw', 'tri', etc. Look at Psychopy gratingstim object for more information: https://www.psychopy.org/api/visual/gratingstim.html#psychopy.visual.GratingStim.tex 
        self.speed = 10.0 #degrees per second - speed that the grating moves in.
        self.orientations = [float(x*45) for x in range(8)] #degrees - a list of directions that the grating will move in. The total number of epochs is equal to the number of orientations times the number of stimulus repetitions.
        self.backgroundColor = [0.0, 0.0, 0.0] #background color of the screen (in RGB). -1.0 equates to 0 and 1.0 equates to 255 for 8 bit colors. For this stimulus, the background is typically only seen between epochs.
        self.stimulusReps = 3 #number of repetitions of the stimulus. Each epoch consists of the grating moving in one direction, so the total number of epochs is the number of orientations times the number of stimulus reps
        self.preTime = 1.0 #seconds - time before the grating starts moving. During this time a static grating appears on the screen
        self.stimTime = 10.0 #seconds - time over which the grating is moving
        self.tailTime = 1.0 #seconds - time after the grating stops moving. During this time a static grating appears on the screen
        self.interStimulusInterval = 1.0 #seconds - the wait time between each epoch. The background color is displayed during this time
        self._angleOffset = 0.0 #reassigned by the experiment in most cases
        
        
    def estimateTime(self):
        '''
        Estimate the total amount of time that this protocol will take to run
        given the current parameters

        Value is stored as total time in seconds in the property 'self._estimatedTime'
        which is initialized by the protocol superclass.

        returns: estimated time in seconds
        '''
        timePerEpoch = self.preTime + self.stimTime + self.tailTime + self.interStimulusInterval
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


    def run(self, win, informationWin):
        '''
        Executes the MovingGratingDirection stimulus
        '''

        self._completed = 0 #started but not completed

        self._informationWin = informationWin #tuple, save here so you don't have to pass this as a function parameter every time you use it


        self.getFR(win)
        self._interStimulusIntervalNumFrames = round(self._FR * self.interStimulusInterval)
        self._actualInterStimulusInterval = self._interStimulusIntervalNumFrames * 1/self._FR

        stimMonitor = win.monitor
        pixPerDeg = self.getPixPerDeg(stimMonitor)

        #Pause for keystroke if the user wants to manually initiate
        if self.userInitiated:
            self.showInformationText(win, 'Stimulus Information: Moving Grating\nPress any key to begin')
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
                self.showInformationText(win, 'Running Moving Grating Direction. Current orientation = ' + \
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
                win.flip()
                if self.checkQuitOrPause():
                    return
            
            if self.writeTTL == 'Pulse':
                self._portObj.baudrate = 1000000
            
            #stim time - flash
            for f in range(self._stimTimeNumFrames):
                grating.phase += self._numCyclesToShiftByFrame
                grating.draw()
                coverRectangle.draw()
                win.flip()
                if self.writeTTL == 'Pulse':
                    self.sendTTL()  #write TTL for every frame flip for this stimulus if in pulse mode
                    
                if self.checkQuitOrPause():
                    return

            #return baudrate to high value
            if self.writeTTL == 'Pulse':
                self._portObj.baudrate = 4000000
                
            #tail time
            for f in range(self._tailTimeNumFrames):
                grating.draw()
                coverRectangle.draw()
                win.flip()
                if self.checkQuitOrPause():
                    return


            self._stimulusEndLog.append(trialClock.getTime())
            self.sendTTL()
            win.flip();win.flip() #two flips to allow for a pause for TTL writing

            self._numberOfEpochsCompleted += 1


        self._completed = 1
