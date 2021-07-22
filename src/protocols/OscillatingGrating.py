# -*- coding: utf-8 -*-
"""
Created on Wed Jul 21 17:18:20 2021

@author: mrsco
"""

"""
Created on Fri Jul 16 12:09:17 2021

@author: mrsco
"""

from protocols.protocol import protocol
from psychopy import core, visual, gui, data, event, monitors
import numpy, math
import serial

class OscillatingGrating(protocol):
    def __init__(self):
        super().__init__()
        self.protocolName = 'OscillatingGrating'
        self.gratingColor = [1.0, 1.0, 1.0]
        self.gratingContrast = 1.0 #multiplied by the color
        self.spatialFrequency = 0.1 #cycles per degree
        self.gratingAmplitude = 1.0
        self.gratingOrientation = 0.0 #degrees
        self.gratingTexture = 'sin' #can be 'sin', 'sqr', 'saw', 'tri', None
        self.oscillationPeriod = 10.0 #seconds
        self.oscillationAmplitude = 10.0 #visual degrees - distance that the grating moves over the course of one oscillation
        self.oscillationPhaseShift = 0.0 #degrees - between 0 and 90 - 90 will start the oscillation in the middle of it's cycle. 0 will start it all the way on one side
        self.backgroundColor = [0.0, 0.0, 0.0]
        self.stimulusReps = 3
        self.preTime = 1.0 #s
        self.stimTime = 10.0 #s
        self.tailTime = 1.0 #s
        self.interStimulusInterval = 1.0 #s - wait time between each stimulus. backGround color is displayed during this time
                
        
    def estimateTime(self):
        '''
        Estimate the total amount of time that this protocol will take to run
        given the current parameters
        
        Value is stored as total time in seconds in the property 'self.estimatedTime'
        which is initialized by the protocol superclass.
        
        returns: estimated time in seconds
        '''
        timePerEpoch = self.preTime + self.stimTime + self.tailTime + self.interStimulusInterval
        numberOfEpochs = self.stimulusReps
        self._estimatedTime = timePerEpoch * numberOfEpochs #return estimated time for the total stimulus in seconds
        
        return self._estimatedTime
      
    
    
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
            return A*math.sin(2*frameNum*math.pi/framesPerCycle + math.radians(phaseShift)) #oscillation can start at the beginning or middle of a cycle: cosine will start it in the middle of a cycle, sin will start it at the beginning
        
        velocity_pixPerFrame = [velocityOnFrameN(f) for f in range(framesPerCycle)]
        return velocity_pixPerFrame 
        
    
    
    def run(self, win, informationWin):
        '''
        Executes the MovingBar stimulus
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
            size = win.size,
            ori = self.gratingOrientation+180,
            sf = (spatialFrequencyCyclesPerPixel, None),
            tex = self.gratingTexture
            )
        
        pixPerFrame = self.determineVelocityByFrame(pixPerDeg)
        cyclesPerFrame = [speed*spatialFrequencyCyclesPerPixel for speed in pixPerFrame] #the number of cycles to move per frame
        #number of cycles to shift the grating by on each frame. In other words phase += numCyclesToShift for each frame
        self._numCyclesToShiftByFrame = [cyclesPerFrame[f%len(cyclesPerFrame)] for f in range(self._stimTimeNumFrames)]

        epochNum = 0
        trialClock = core.Clock() #this will reset every trial
        for stim in range(self.stimulusReps):
            epochNum += 1
        
            #show information if necessary
            if self._informationWin[0]:
                self.showInformationText(win, 'Running Flash\n Epoch ' + str(epochNum) + ' of ' + str(self.stimulusReps))
            
            #pause for inter stimulus interval
            win.color = self.backgroundColor
            for f in range(self._interStimulusIntervalNumFrames):
                win.flip()
                if self.checkQuit():
                    return
                    
            #pretime... stationary grating
            self._stimulusStartLog.append(trialClock.getTime())
            self.sendTTL()
            self._numberOfEpochsStarted += 1
            for f in range(self._preTimeNumFrames):
                grating.draw()
                win.flip()
                if self.checkQuit():
                    return
            
            #stim time - flash
            for f in range(self._stimTimeNumFrames):
                grating.phase +=  self._numCyclesToShiftByFrame[f]
                grating.draw()
                win.flip()
                if self.checkQuit():
                    return
            
            #tail time
            win.color = self.backgroundColor
            for f in range(self._tailTimeNumFrames):
                grating.draw()
                win.flip()
                if self.checkQuit():
                    return
        
            
            self._stimulusEndLog.append(trialClock.getTime())
            self.sendTTL()
            
            self._numberOfEpochsCompleted += 1
                
            
        self._completed = 1