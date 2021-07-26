# -*- coding: utf-8 -*-
"""
Created on Mon Jul 12 16:17:29 2021

Grating moves across the screen in directions specified in orientations parameter.
Order is random.

@author: mrsco
"""
from protocols.protocol import protocol
from psychopy import core, visual, gui, data, event, monitors
import serial, random, math

class MovingGratingDirection(protocol):
    def __init__(self):
        super().__init__()
        self.protocolName = 'MovingGratingDirection'
        self.gratingColor = [1.0, 1.0, 1.0]
        self.gratingContrast = 1.0 #multiplied by the color
        self.spatialFrequency = 0.1 #cycles per degree
        self.gratingAmplitude = 1.0
        self.gratingTexture = 'sin' #can be 'sin', 'sqr', 'saw', 'tri', None
        self.speed = 10.0 #deg/s
        self.orientations = [float(x*45) for x in range(8)] #list of floats - degrees
        self.backgroundColor = [0.0, 0.0, 0.0]
        self.stimulusReps = 3
        self.preTime = 1.0 #s
        self.stimTime = 10.0 #s
        self.tailTime = 1.0 #s
                
        
    def estimateTime(self):
        '''
        Estimate the total amount of time that this protocol will take to run
        given the current parameters
        
        Value is stored as total time in seconds in the property 'self.estimatedTime'
        which is initialized by the protocol superclass.
        
        returns: estimated time in seconds
        '''
        timePerEpoch = self.preTime + self.stimTime + self.tailTime
        numberOfEpochs = self.stimulusReps
        self._estimatedTime = timePerEpoch * numberOfEpochs #return estimated time for the total stimulus in seconds
        
        return self._estimatedTime
      
    
    
    def createOrientationLog(self):
        '''
        Generate a random sequence of orientations given the desired orientations
        
        Desired orientations are specified as a list in self.orientations
        
        creates self.orientationLog, a list, which specifies the orienation 
        to use for each epoch
        '''
        orientations = self.orientations
        self.orientationLog = []
        random.seed(self.randomSeed) #reinitialize the random seed
        
        for n in range(self.stimulusReps):
            self.orientationLog += random.sample(orientations, len(orientations))
            
    
    def run(self, win, informationWin):
        '''
        Executes the MovingBar stimulus
        '''

        self._completed = 0 #started but not completed
        
        self._informationWin = informationWin #tuple, save here so you don't have to pass this as a function parameter every time you use it
        
        
        self.getFR(win)
        
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
            sf = (spatialFrequencyCyclesPerPixel, None),
            tex = self.gratingTexture
            )
        
        self._numCyclesToShiftByFrame = self.speed*self.spatialFrequency*(1/self._FR)
        
        self.createOrientationLog()

        totalEpochs = len(self.orientationLog)
        epochNum = 0
        trialClock = core.Clock() #this will reset every trial
        
        for ori in self.orientationLog:
            grating.ori = -ori #flip for coordinate convention: 0 = east, 90 = north, 180 = west, 270 = south
            epochNum += 1
            print(ori)
            #show information if necessary
            if self._informationWin[0]:
                self.showInformationText(win, 'Running Moving Grating Direction. Current orientation = ' + \
                                         str(ori) + '\n Epoch ' + str(epochNum) + ' of ' + str(totalEpochs))
                    
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
                grating.phase += self._numCyclesToShiftByFrame
                grating.draw()
                win.flip()
                if self.checkQuit():
                    return
            
            #tail time
            for f in range(self._tailTimeNumFrames):
                grating.draw()
                win.flip()
                if self.checkQuit():
                    return
        
            
            self._stimulusEndLog.append(trialClock.getTime())
            self.sendTTL()
            
            self._numberOfEpochsCompleted += 1
                
            
        self._completed = 1