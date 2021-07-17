# -*- coding: utf-8 -*-
"""
Created on Thu Jul 15 13:35:56 2021

Flash intensities of different magnitudes

@author: mrsco
"""

from protocols.protocol import protocol
import random
from psychopy import core, visual, gui, data, event, monitors
import math
import numpy as np
import serial

class FlashFamily(protocol):
    def __init__(self):
        super().__init__()
        self.protocolName = 'FlashFamily'
        self.backgroundColor = [-1.0, -1.0, -1.0] #the 'mean' light level that displays between flashes
        self.stepSizes = [0.1, 0.2, 0.4, 0.8, 1.4, 1.6, 2] #each flash intensity will be the background color + a stepSize
        self.stimulusReps = 3 #times through the stimulus
        self.preTime = 0.5 #s
        self.stimTime = 0.5 #s
        self.tailTime = 0.5#s
        self.interFamilyInterval = 5 #s - wait time between each flash family. backGround color is displayed during this time
                
        
    def estimateTime(self):
        '''
        Estimate the total amount of time that this protocol will take to run
        given the current parameters
        
        Value is stored as total time in seconds in the property 'self.estimatedTime'
        which is initialized by the protocol superclass.
        
        returns: estimated time in seconds
        '''
        timePerEpoch = self.preTime + self.stimTime + self.tailTime
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
        

        #Pause for keystroke if the user wants to manually initiate
        if self.userInitiated:
            self.showInformationText(win, 'Stimulus Information: Flash Family \nPress any key to begin')
            event.waitKeys() #wait for key press

        winWidth = win.size[0]
        winHeight = win.size[1]        
        
        self.flashWidth_deg = winWidth/pixPerDeg
        self.flashHeight_deg = winHeight/pixPerDeg
        
        
        self.flashLog = [] #holds the single value intensity for each flash to be played, in the order that they will be played
        for fam in range(self.stimulusReps):
            for step in self.stepSizes:
                self.flashLog.append(self.backgroundColor[0] + step)
        

        intensityList = [[size, size, size] for size in self.flashLog[0:len(self.stepSizes)]] #List of list corresponding to color to assign to win object for each flash in one family
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
                allKeys = event.getKeys() #check if user wants to quit early
                if len(allKeys)>0:
                    if 'q' in allKeys:
                        return
            
            for stepNum in range(len(self.stepSizes)):
                
                self._stimulusStartLog.append(trialClock.getTime())
                
                #pretime... nothing happens
                for f in range(self._preTimeNumFrames):
                    win.flip()
                    allKeys = event.getKeys() #check if user wants to quit early
                    if len(allKeys)>0:
                        if 'q' in allKeys:
                            return
            
                #stim time
                win.color = intensityList[stepNum] #set flash intensity
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