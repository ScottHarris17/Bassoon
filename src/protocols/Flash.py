# -*- coding: utf-8 -*-
"""
Created on Fri Jul 16 12:09:17 2021

@author: mrsco
"""

from protocols.protocol import protocol
from psychopy import core, visual, data, event, monitors
import numpy
import serial

class Flash(protocol):
    def __init__(self):
        super().__init__()
        self.protocolName = 'Flash' #The flash protocol presents a full field flash on the screen for a specified amount of time
        self.flashIntensity = [1.0, 1.0, 1.0] #intensity of the screen (in RGB) during the flash. -1.0 equates to 0 and 1.0 equates to 255 for 8 bit colors.
        self.backgroundColor = [-1.0, -1.0, -1.0] #background color of the screen before/after the flash  (in RGB). -1.0 equates to 0 and 1.0 equates to 255 for 8 bit colors.
        self.stimulusReps = 3 #number of repetitions
        self.preTime = 1.0 #seconds - the amount of time before the flash on each epoch, during which the background is shown
        self.stimTime = 5.0 #seconds - the amount of time that the flash lasts for
        self.tailTime = 1.0 #seconds - the amount of time after the flash on each epoch, during which the background is shown
        self.interStimulusInterval = 1.0 #seconds - the wait time between each epoch. The background color is displayed during this time.
                
        
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
      
            
    def run(self, win, informationWin):
        '''
        Executes the Flash stimulus
        '''

        self._completed = 0 #started but not completed
        
        self._informationWin = informationWin #tuple, save here so you don't have to pass this as a function parameter every time you use it
        
        
        self.getFR(win)
        self._interStimulusIntervalNumFrames = round(self._FR * self.interStimulusInterval)
        self._actualInterStimulusInterval = self._interStimulusIntervalNumFrames * 1/self._FR
        
        
        #Pause for keystroke if the user wants to manually initiate
        if self.userInitiated:
            self.showInformationText(win, 'Stimulus Information: Flash\nPress any key to begin')
            event.waitKeys() #wait for key press  
        
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
                if self.checkQuitOrPause():
                    return
                    
            #pretime... nothing happens
            self._stimulusStartLog.append(trialClock.getTime())
            self.sendTTL()
            self._numberOfEpochsStarted += 1
            for f in range(self._preTimeNumFrames):
                win.flip()
                if self.checkQuitOrPause():
                    return
            
            #stim time - flash
            win.color = self.flashIntensity
            for f in range(self._stimTimeNumFrames):
                win.flip()
                if self.checkQuitOrPause():
                    return
            
            #tail time
            win.color = self.backgroundColor
            for f in range(self._tailTimeNumFrames):
                win.flip()
                if self.checkQuitOrPause():
                    return
        
            
            self._stimulusEndLog.append(trialClock.getTime())
            self.sendTTL()
            
            self._numberOfEpochsCompleted += 1
                
        self._completed = 1
