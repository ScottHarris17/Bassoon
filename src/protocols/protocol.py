# -*- coding: utf-8 -*-
"""
Created on Fri Jul  9 17:24:45 2021

@author: mrsco
"""
from psychopy import core, visual, gui, data, event, monitors
import random, math

class protocol():
    def __init__(self):
        self.suffix = '_' #suffix for the protocol name, begin with _
        self.userInitiated = False #determines whether a key stroke is needed to initiate the protocol. Will be set to the corresponding experiment value of the experiment if not updated by the user
        
        self._stimulusStartLog = []
        self._stimulusEndLog = []
        self._pauseTimeLog = []
        
        self.randomSeed = random.random()
        
        self.tagList = [] #list of tags for the protocol
        
        self._estimatedTime = 0.0 #estimated time in seconds that this stimulus will take. There should be a corresponding function self.estimateTime() that sets this number
        
        self._numberOfEpochsStarted = 0
        self._numberOfEpochsCompleted = 0 #counts the number of epochs that have actually occured
        
        self._completed = -1 # -1 indicates stimulus never ran. 0 indicates stimulus started but ended early. 1 indicates stimulus ran to completion
        
        

    def estimateTime(self):
        '''
        estimateTime place holder. Should be overriden in subclass
        '''
        return 0
    
    
    def getFR(self, win):
        '''
        Determine the frame rate of the win object (e.g. stimulus monitor) and
        calculate number of frames and total time for each segment of the stimulus
        '''
        
        self._FR = win.getActualFrameRate()

        self._preTimeNumFrames = round(self._FR*self.preTime)
        self._stimTimeNumFrames = round(self._FR*self.stimTime)
        self._tailTimeNumFrames = round(self._FR*self.tailTime)

        self._actualPreTime = self._preTimeNumFrames * 1/self._FR
        self._actualStimTime = self._stimTimeNumFrames * 1/self._FR
        self._actualTailTime = self._tailTimeNumFrames * 1/self._FR
        
    def getPixPerDeg(self, stimMonitor):
        '''
        determine the pixels per degree for the stimulus monitor
        '''
        
        mon = monitors.Monitor(stimMonitor.name)
        eyeDistance = mon.getDistance()
        numPixelsWide = mon.currentCalib['sizePix'][0]
        cmWide = mon.currentCalib['width']
        totalVisualDegrees = 2*math.degrees(math.atan((cmWide/2)/eyeDistance))
        return numPixelsWide/totalVisualDegrees
    
    def showInformationText(self, stimWin, txt):
        '''
        update the information window
        '''
        if self._informationWin[0]:
            win = self._informationWin[1]
        else:
            win = stimWin
        
        informationalText = visual.TextStim(
                                    win = win, 
                                    text = txt)

        informationalText.draw()
        win.flip()

    def checkQuit(self):
        '''
        Checks if user wants to quit early during a stimulus. Press 'q' key to quit early
        '''
        allKeys = event.getKeys() #check if user wants to quit early
        if len(allKeys)>0:
            if 'q' in allKeys:
                self.stoppedEarly = 1
                return 1
        return 0
            
    
    def sendTTL(self):
        '''
        sends ttl pulse during experiment if the setting is turned on
        '''
        if self.writeTTL:
            try:
                self._portObj.write(0X4B) #self.port_Obj is initialized in the experiment.activate() method
            except:
                print('***WARNING: TTL Pulse Failed***')
        return


