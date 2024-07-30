# -*- coding: utf-8 -*-
"""
Created on Thu Jul 15 13:35:56 2021

Flash intensities of different magnitudes

@author: mrsco
"""

from protocols.protocol import protocol
import random
from psychopy import core, visual, data, event, monitors
import math
import numpy as np
import serial

class FlashFamily(protocol):
    def __init__(self):
        super().__init__()
        self.protocolName = 'FlashFamily' #The flash family consists of full field flashes of varying intensity.
        self.backgroundColor = [-1.0, -1.0, -1.0] #the baseline light level that displays before, after, and between flashes (in RGB). -1.0 equates to 0 and 1.0 equates to 255 for 8 bit colors.
        self.stepSizes = [0.1, 0.2, 0.4, 0.8, 1.4, 1.6, 2] #each flash intensity will be the background color + a stepSize. Stepsizes are additive to all RGB channels, so currently color cannot be changed (though this is easy to implement if you want to modify the protocol script or create a new one). Note that the stepSize + backgroundColor should always be between -1.0 and 1.0. Steps are played in the order they are specified here.
        self.stimulusReps = 3 #number of times through the stimulus. Each repetition consists of a cycle through each step, so the total number of epochs is equal to the number of step sizes times the number of stimulus reps.
        self.preTime = 0.5 #seconds - the amount of time before each flash starts playing. During this time, the background color is shown (each flash, even within a family, is treated as its own epoch, with a pretime, stimtime, and tailtime).
        self.stimTime = 0.5 #seconds - the amount of time that each flash plays for (each flash, even within a family, is treated as its own epoch, with a pretime, stimtime, and tailtime).
        self.tailTime = 0.5#seconds - the amount of time to wait after each flash before moving onto the next epoch. During this time, the background color is shown (each flash, even within a family, is treated as its own epoch, with a pretime, stimtime, and tailtime).
        self.interFamilyInterval = 5 #seconds - the wait time between each epoch. The background color is displayed during this time.
        self.interFlashInterval = 0.5 #seconds - the wait time between each flash within a family (should be nonzero to ensure TTL writing)
        
    def estimateTime(self):
        '''
        Estimate the total amount of time that this protocol will take to run
        given the current parameters
        
        Value is stored as total time in seconds in the property 'self.estimatedTime'
        which is initialized by the protocol superclass.
        
        returns: estimated time in seconds
        '''
        timePerEpoch = self.preTime + self.stimTime + self.tailTime + self.interFlashInterval
        numberOfEpochs = len(self.stepSizes) * self.stimulusReps
        interFamilyTime = self.interFamilyInterval * len(self.stepSizes)
        
        self._estimatedTime = timePerEpoch * numberOfEpochs + interFamilyTime #return estimated time for the total stimulus in seconds
        
        return self._estimatedTime
            
    
    
    def run(self, win, informationWin):
        '''
        Executes the FlashFamily stimulus
        '''

        self._completed = 0
        
        self._informationWin = informationWin #tuple, save here so you don't have to pass this as a function parameter every time you use it
        
        stimMonitor = win.monitor
        pixPerDeg = self.getPixPerDeg(stimMonitor)
        
        self.getFR(win)
        self._interFamilyIntervalNumFrames = round(self._FR * self.interFamilyInterval)
        self._actualInterFamilyInterval = self._interFamilyIntervalNumFrames * 1/self._FR
        self._interFlashIntervalNumFrames = round(self._FR * self.interFlashInterval)
        self._actualInterFlashInterval = self._interFlashIntervalNumFrames * 1/self._FR

        #Pause for keystroke if the user wants to manually initiate
        if self.userInitiated:
            self.showInformationText(win, 'Stimulus Information: Flash Family \nPress any key to begin')
            event.waitKeys() #wait for key press

        winWidth = win.size[0]
        winHeight = win.size[1]        
        
        self.flashWidth_deg = winWidth/pixPerDeg
        self.flashHeight_deg = winHeight/pixPerDeg
        
        
        self._flashLog = [] #holds the single value intensity for each flash to be played, in the order that they will be played
        for fam in range(self.stimulusReps):
            for step in self.stepSizes:
                self._flashLog.append(self.backgroundColor[0] + step)
        

        intensityList = [[size, size, size] for size in self._flashLog[0:len(self.stepSizes)]] #List of list corresponding to color to assign to win object for each flash in one family
        epochNum = 0
        
        trialClock = core.Clock() #this will reset every trial
        for i in range(self.stimulusReps):
            
            
            #show information if necessary
            if self._informationWin[0]:
                self.showInformationText(win, 'Running Flash Family. Current Family = ' + \
                                         str(i+1) + ' of ' + str(self.stimulusReps))
            
                
            #pause for interfamily interval
            win.color = self.backgroundColor
            for f in range(self._interFamilyIntervalNumFrames):
                win.flip()
                if self.checkQuitOrPause():
                        return
            
            for stepNum in range(len(self.stepSizes)):
                
                #pause for inter stimulus interval
                win.color = self.backgroundColor
                for f in range(self._interFlashIntervalNumFrames):
                    win.flip()
                    if self.checkQuitOrPause():
                        return
                
                self._stimulusStartLog.append(trialClock.getTime())
                self.sendTTL()
                self._numberOfEpochsStarted += 1
                #pretime... nothing happens
                win.color = self.backgroundColor
                for f in range(self._preTimeNumFrames):
                    win.flip()
                    if self.checkQuitOrPause():
                        return
            
                #stim time
                win.color = intensityList[stepNum] #set flash intensity
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