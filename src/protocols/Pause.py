# -*- coding: utf-8 -*-
"""
Created on Fri Jul 16 12:43:47 2021

@author: mrsco
"""

from protocols.protocol import protocol
from psychopy import core, visual,data, event, monitors
import numpy
import serial

class Pause(protocol):
    def __init__(self):
        super().__init__()
        self.protocolName = 'Pause'
        self.backgroundColor = [-1.0, -1.0, -1.0]
        self.preTime = 1.0 #s
        self.stimTime = 5.0 #s
        self.tailTime = 1.0#s
                
        
    def estimateTime(self):
        '''
        Estimate the total amount of time that this protocol will take to run
        given the current parameters
        
        Value is stored as total time in seconds in the property 'self.estimatedTime'
        which is initialized by the protocol superclass.
        
        returns: estimated time in seconds
        '''
        timePerEpoch = self.preTime + self.stimTime + self.tailTime
        self._estimatedTime = timePerEpoch #return estimated time for the total stimulus in seconds
        
        return self._estimatedTime
      
            
    def run(self, win, informationWin):
        '''
        Executes the MovingBar stimulus
        '''

        self._completed = 0 #started but not completed
        
        self._informationWin = informationWin #tuple, save here so you don't have to pass this as a function parameter every time you use it
        
        
        self.getFR(win)
        
                
        #Pause for keystroke if the user wants to manually initiate
        if self.userInitiated:
            self.showInformationText(win, 'Stimulus Information: Pause\nPress any key to begin')
            event.waitKeys() #wait for key press  
        
        
        trialClock = core.Clock() #initiate clock
        
        #show information if necessary
        if self._informationWin[0]:
            self.showInformationText(win, 'Pausing for ' + str(self._estimatedTime) + 's')
        

        win.color = self.backgroundColor

                
        #pretime... nothing happens
        self._stimulusStartLog.append(trialClock.getTime())
        self.sendTTL()
        self._numberOfEpochsStarted += 1
        for f in range(self._preTimeNumFrames):
            win.flip()
            if self.checkQuit():
                return
        
        #stim time
        for f in range(self._stimTimeNumFrames):
            win.flip()
            if self.checkQuit():
                return
        
        #tail time
        win.color = self.backgroundColor
        for f in range(self._tailTimeNumFrames):
            win.flip()
            if self.checkQuit():
                return
    
        
        self._stimulusEndLog.append(trialClock.getTime())
        self.sendTTL()
        
        self._numberOfEpochsCompleted += 1
            
            
        self._completed = 1