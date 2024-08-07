# -*- coding: utf-8 -*-
"""
Created on Wed Jul 21 17:18:20 2021

Grating oscillates back and forth across the screen. The oscillation is sinusoidal.
oscillationAmplitude is the total distance covered by 1/2 oscillation cycle (in visual degrees).
oscillationPeriod is the amount of time it takes to complete one full oscillation cycle (total distance covered = amplitude * 2)


@author: mrsco
"""

from protocols.protocol import protocol
from psychopy import core, visual, data, event, monitors
import math, random
import serial
import numpy as np

class OscillatingGrating(protocol):
    def __init__(self):
        super().__init__()
        self.protocolName = 'OscillatingGrating' #During the Oscillating Grating stimulus a grating pattern oscillates sinusoidally over time
        self.gratingColor = [1.0, 1.0, 1.0]#color of the grating (in RGB).-1.0 equates to 0 and 1.0 equates to 255 for 8 bit colors.
        self.gratingContrast = 1.0 #Sets the contrast of the grating by multiplying by the the grating color.
        self.meanIntensity = 0.0 #The mean intensity of the grating. This value should be between -1 and 1.0, where 0.0 is "middle gray"
        self.spatialFrequency = 0.15 #cycles per degree - the spatial frequency of the grating.
        self.gratingOrientations = [90.0, 270.0]  #degrees - a list of directions that the grating will move in. Because the oscillating grating moves in two directions per epoch, these numbers define the starting direction.
        self.gratingTexture = 'sin' #The pattern of the grating. This can be 'sin', 'sqr', 'saw', 'tri', etc. Look at Psychopy gratingstim object for more information: https://www.psychopy.org/api/visual/gratingstim.html#psychopy.visual.GratingStim.tex 
        self.oscillationPeriod = 15.0 #seconds - the time it takes to complete a full oscillation cycle
        self.oscillationAmplitude = 20.0 #visual degrees - distance that the grating moves over the course of one half oscillation
        self.oscillationPhaseShift = 0.0 #degrees - between 0 and 90 - 90 will start the oscillation in the middle of it's cycle (cosine function). 0 will start it all the way on one side (sine function)
        self.backgroundColor = [0.0, 0.0, 0.0] #background color of the screen (in RGB). -1.0 equates to 0 and 1.0 equates to 255 for 8 bit colors. For this stimulus, the background is typically only seen between epochs.
        self.stimulusReps = 3 #number of repetitions of the stimulus. Each epoch consists of the grating oscillating in one orientation, so the total number of epochs is the number of grating orientations times the number of stimulus reps
        self.preTime = 1.0 # seconds - time before the grating starts moving. During this time a static grating appears on the screen
        self.stimTime = 10.0 #seconds - time over which the grating is oscillating. The number of oscillation cycles fully completed is equal to the stim time divided by the oscillation period
        self.tailTime = 1.0 #seconds - time after the grating stops moving. During this time a static grating appears on the screen
        self.interStimulusInterval = 1.0 #seconds - the wait time between each epoch. The background color is displayed during this time
        self._angleOffset = 0.0 #reassigned by experiment in most cases
        
    
   
    def estimateTime(self):
        '''
        Estimate the total amount of time that this protocol will take to run
        given the current parameters
        
        Value is stored as total time in seconds in the property 'self.estimatedTime'
        which is initialized by the protocol superclass.
        
        returns: estimated time in seconds
        '''
        timePerEpoch = self.preTime + self.stimTime + self.tailTime + self.interStimulusInterval
        numberOfEpochs = self.stimulusReps * len(self.gratingOrientations)
        self._estimatedTime = timePerEpoch * numberOfEpochs #return estimated time for the total stimulus in seconds
        
        return self._estimatedTime
      
        
    def createOrientationLog(self):
        '''
        Generate a random sequence of orientations given the desired orientations
        
        Desired orientations are specified as a list in self.orientations
        
        creates self._orientationLog, a list, which specifies the orienation 
        to use for each epoch
        '''
        orientations = self.gratingOrientations
        self._orientationLog = []
        random.seed(self.randomSeed) #reinitialize the random seed
        
        for n in range(self.stimulusReps):
            self._orientationLog += random.sample(orientations, len(orientations))
            
            
    def determineVelocityByFrame(self, pixPerDeg):
        '''
        Determine the phase shift to move the grating on each frame
        '''
        self._oscillationFrequency = 1/self.oscillationPeriod
        
        framesPerCycle = int(self._FR * (1/self._oscillationFrequency))
        
        totalDistance_pix = self.oscillationAmplitude * pixPerDeg #total pixels that the grating moves by for one half cycle
        
        #frame number vs velocity is described by a sin wave. Integral of Asin(2pi*frameNum/framesPerCycle) evaluated from 0 to framesPerCycle/2 should equal totalDistance_pix
        #A = pi*totalDistance_pix/(framesPerCycle)
        A = math.pi*totalDistance_pix/framesPerCycle
        
        #normalize the velocity phase shift to be between 0 and 90 degrees if need be
        if self.oscillationPhaseShift > 90 or self.oscillationPhaseShift < 0:
            self.oscillationPhaseShift = abs(math.degrees(math.asin(math.sin(math.radians(self.oscillationPhaseShift)))))
            print('oscillationPhaseShift parameter not within bounds, correcting to ', self.oscillationPhaseShift, 'degrees')
            
        def velocityOnFrameN(frameNum, A = A, framesPerCycle = framesPerCycle, phaseShift = self.oscillationPhaseShift):
            return A*math.sin(2*frameNum*math.pi/framesPerCycle + math.radians(phaseShift)) 
        
        velocity_pixPerFrame = [velocityOnFrameN(f) for f in range(framesPerCycle)]
        return velocity_pixPerFrame 
    
      
    
    def run(self, win, informationWin):
        '''
        Executes the OscillatingGrating stimulus
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
            self.showInformationText(win, 'Stimulus Information: Oscillating Grating\nPress any key to begin')
            event.waitKeys() #wait for key press  
        
        spatialFrequencyCyclesPerPixel = self.spatialFrequency * (1/pixPerDeg)
        
        grating = visual.GratingStim(
            win,
            size = (win.size[0]*2, win.size[1]*2),
            ori = 0, #self.gratingOrientation + 180 - self._angleOffset,
            sf = (spatialFrequencyCyclesPerPixel, None),
            tex = self.gratingTexture,
            contrast = self.gratingContrast,
            color = self.gratingColor
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
            
            
        self.createOrientationLog()
        pixPerFrame = self.determineVelocityByFrame(pixPerDeg)
        cyclesPerFrame = [speed*spatialFrequencyCyclesPerPixel for speed in pixPerFrame] #the number of cycles to move per frame
        #number of cycles to shift the grating by on each frame. In other words phase += numCyclesToShift for each frame
        self._numCyclesToShiftByFrame = [cyclesPerFrame[f%len(cyclesPerFrame)] for f in range(self._stimTimeNumFrames)]
        
        epochNum = 0
        trialClock = core.Clock() #this will reset every trial
        for ori in self._orientationLog:
            epochNum += 1
            
            grating.ori = -ori - self._angleOffset
            
            #show information if necessary
            if self._informationWin[0]:
                self.showInformationText(win, 'Running Oscillating Grating. Orientation = ' +  str(ori) + '\n Epoch ' + str(epochNum) + ' of ' + str(len(self._orientationLog)))
            
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
            
            #stim time - flash
            for f in range(self._stimTimeNumFrames):
                grating.phase += self._numCyclesToShiftByFrame[f]
                grating.draw()
                coverRectangle.draw()
                win.flip()
                if self.checkQuitOrPause():
                    return
            
            #tail time
            win.color = self.backgroundColor
            for f in range(self._tailTimeNumFrames):
                grating.draw()
                coverRectangle.draw()
                win.flip()
                if self.checkQuitOrPause():
                    return
        
            
            self._stimulusEndLog.append(trialClock.getTime())
            self.sendTTL()
            win.flip();win.flip() #two flips in to allow for a pause for TTL writing
            
            self._numberOfEpochsCompleted += 1
                
            
        self._completed = 1