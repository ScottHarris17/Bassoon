# -*- coding: utf-8 -*-
"""
Created on Fri Jul 16 12:09:17 2021

@author: mrsco
"""

from protocols.protocol import protocol
from psychopy import core, visual, gui, data, event, monitors
import numpy
import serial

class Flash(protocol):
    def __init__(self):
        super().__init__()
        self.protocolName = 'Flash'
        self.flashIntensity = [1.0, 1.0, 1.0]
        self.backgroundColor = [-1.0, -1.0, -1.0]
        self.stimulusReps = 3
        self.preTime = 1.0 #s
        self.stimTime = 5.0 #s
        self.tailTime = 1.0#s
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
      
            
    def run(self, win, informationWin):
        '''
        Executes the MovingBar stimulus
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
                allKeys = event.getKeys() #check if user wants to quit early
                if len(allKeys)>0:
                    if 'q' in allKeys:
                        return
                    
            #pretime... nothing happens
            self._stimulusStartLog.append(trialClock.getTime())
            for f in range(self._preTimeNumFrames):
                win.flip()
                allKeys = event.getKeys() #check if user wants to quit early
                if len(allKeys)>0:
                    if 'q' in allKeys:
                        return
            
            #stim time - flash
            win.color = self.flashIntensity
            for f in range(self._stimTimeNumFrames):
                win.flip()
                allKeys = event.getKeys() #check if user wants to quit early
                if len(allKeys)>0:
                    if 'q' in allKeys:
                        return
            
            #tail time
            win.color = self.backgroundColor
            for f in range(self._tailTimeNumFrames):
                win.flip()
                allKeys = event.getKeys() #check if user wants to quit early
                if len(allKeys)>0:
                    if 'q' in allKeys:
                        return
        
            
            self._stimulusEndLog.append(trialClock.getTime())
            
            self._numberOfEpochsCompleted += 1
                
            
        self._completed = 1