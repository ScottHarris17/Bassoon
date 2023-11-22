# -*- coding: utf-8 -*-
"""
Created on Fri Jul  9 17:24:45 2021

@author: mrsco
"""
from psychopy import core, visual, data, event, monitors
import time
import random, math

class protocol():
    def __init__(self):
        self.suffix = '_' #suffix for the protocol name, begin with _
        self.userInitiated = False #determines whether a key stroke is needed to initiate the protocol. Will be set to the corresponding experiment value if not updated by the user
        
        self._stimulusStartLog = []
        self._stimulusEndLog = []
        self._pauseTimeLog = []
        
        self.randomSeed = random.random()
        
        self.tagList = [] #list of tags for the protocol
        
        self._estimatedTime = 0.0 #estimated time in seconds that this stimulus will take. There should be a corresponding function self.estimateTime() that sets this number
        
        self._numberOfEpochsStarted = 0
        self._numberOfEpochsCompleted = 0 #counts the number of epochs that have actually occured
        
        self._timesTTLFlipped = 0 #counts the number of TTL flips, used for sustained mode only
        self._timesTTLFlippedBookmark = 0 #counts the number of TTL flips during bookmark (sustained mode with bookmarking only)
        
        self._userPauseCount = 0 #counts the number of times the user initiated a pause in the middle of the stimulus
        self._userPauseDurations = [] #list of amount of time (in seconds) that each pause lasted for
        
        self._completed = -1 # -1 indicates stimulus never ran. 0 indicates stimulus started but ended early. 1 indicates stimulus ran to completion
        
        

    def estimateTime(self):
        '''
        estimateTime place holder. Should be overriden in subclass
        '''
        return 0
    
    
    def getFR(self, win):
        '''
        Determine the frame rate of the win object (e.g. stimulus monitor) and calculate number of frames and total time for each segment of the stimulus
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

    def checkQuitOrPause(self):
        '''
        Checks if user wants to quit early during a stimulus or pause the stimulus. Press 'q' key to quit early. Press 'p' to pause the stimulus''
        '''
        allKeys = event.getKeys() #check if user wants to quit early
        if len(allKeys)>0:
            if 'q' in allKeys:
                self._stoppedEarly = 1
                print('*** Quiting stimulus early')
                return 1
            elif 'p' in allKeys:
                self._userPauseCount += 1
                print('*** STIMULUS HAS PAUSED. Press any key to resume')
                startTime = time.time()
                event.waitKeys() #wait for key press to resume
                endTime = time.time()
                pauseTime = endTime - startTime
                print('*** Resuming Stimulus. Total pause time was %s seconds' % pauseTime)
                self._userPauseDurations.append(pauseTime)
                return 0
            
        return 0
            
    
    def sendTTL(self, bookmark = False):
        '''
        sends ttl pulse during experiment if the setting is turned on TTL pulse or sustained can be selected. If pulse is turned on, this only executes during a protocol, but not before.
        '''
        if self.writeTTL == 'Pulse':
                try:
                    self._portObj.write(0X4B) #self._portObj is initialized in the experiment.activate() method
                except:
                    print('***WARNING: TTL Pulse Failed***')
        
        elif self.writeTTL == 'Sustained':
            if bookmark:
                self._timesTTLFlippedBookmark += 1
            else:
                self._timesTTLFlipped += 1
                
            if self._TTLON: #IF TTL is ON, turn it OFF
                self._portObj.setRTS(True) #'True' turns TTL off on picolo
                self._TTLON = False
            else: # If TTL is OFF, turn it ON
                self._portObj.setRTS(False) #'False' turns TTL ON on picolo
                self._TTLON = True
        return
    
    
    def burstTTL(self, win):
        '''
        sends a burst of TTL pulses at the start of a stimulus when the the TTL port is in pulse mode. As of 10/29/2023 this appears to only be implemented for checkerboard receptive field and flash grid. The stereotyped busrt is 20 TTL pulses at frame rate, wait 0.2 seconds, and 20 more TTL pulses at frame rate
        '''
        if self.writeTTL != 'Pulse':
            return
        
        for i in range(20):
            self.sendTTL()
            win.flip()
            
        core.wait(0.2)
        
        for i in range(20):
            self.sendTTL()
            win.flip()
        
        return