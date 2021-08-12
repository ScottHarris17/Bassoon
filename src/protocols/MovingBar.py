# -*- coding: utf-8 -*-
"""
Created on Fri Jul  9 17:27:32 2021

Bar moves across the screen at a given speed in each of n directions

@author: mrsco
"""
from protocols.protocol import protocol
import random
from psychopy import core, visual,  data, event, monitors
import math
import numpy
import serial

class MovingBar(protocol):
    def __init__(self):
        super().__init__()
        self.protocolName = 'MovingBar'
        self.orientations = [float(x*45) for x in range(8)]
        self.barWidth = 3.23 #deg
        self.barHeight = 100.0 #deg
        self.speed = 10.0 #deg/s
        self.barColor = [1.0, 1.0, 1.0]
        self.backgroundColor = [-1.0, -1.0, -1.0]
        self.stimulusReps = 3
        self.preTime = 1.0 #s
        self.stimTime = 5.0 #s
        self.tailTime = 1.0#s
        self.interStimulusInterval = 1.0 #s - wait time between each stimulus. backGround color is displayed during this time

        self._angleOffset = 0.0 #deg - reassigned by the experiment in most cases
                
        
    def estimateTime(self):
        '''
        Estimate the total amount of time that this protocol will take to run
        given the current parameters
        
        Value is stored as total time in seconds in the property 'self.estimatedTime'
        which is initialized by the protocol superclass.
        
        returns: estimated time in seconds
        '''
        timePerEpoch = self.preTime + self.stimTime + self.tailTime + self.interStimulusInterval
        numberOfEpochs = len(self.orientations) * self.stimulusReps
        self._estimatedTime = timePerEpoch * numberOfEpochs #return estimated time for the total stimulus in seconds
        
        return self._estimatedTime
      
        
    def createOrientationLog(self):
        '''
        Generate a random sequence of orientations given the desired orientations
        
        Desired orientations are specified as a list in self.orientations
        
        creates self._orientationLog, a list, which specifies the orienation 
        to use for each epoch
        '''
        orientations = self.orientations
        self._orientationLog = []
        random.seed(self.randomSeed) #reinitialize the random seed
        
        for n in range(self.stimulusReps):
            self._orientationLog += random.sample(orientations, len(orientations))
            
            
            
    def run(self, win, informationWin):
        '''
        Executes the MovingBar stimulus
        '''

        self._completed = 0
        
        self._informationWin = informationWin #tuple, save here so you don't have to pass this as a function parameter every time you use it
        
        stimMonitor = win.monitor
        pixPerDeg = self.getPixPerDeg(stimMonitor)
        self.getFR(win)
        self._interStimulusIntervalNumFrames = round(self._FR * self.interStimulusInterval)
        self._actualInterStimulusInterval = self._interStimulusIntervalNumFrames * 1/self._FR
        
        barHeightPix = pixPerDeg *self.barHeight
        barWidthPix = pixPerDeg * self.barWidth
        
        #Pause for keystroke if the user wants to manually initiate
        if self.userInitiated:
            self.showInformationText(win, 'Stimulus Information: Moving Bar\nPress any key to begin')
            event.waitKeys() #wait for key press

        winWidth = win.size[0]
        winHeight = win.size[1]
        winCenter = [0, 0]
        winRadius = ((winWidth/2)**2 + (winHeight/2)**2)**0.5
        pixPerFrame = self.speed * pixPerDeg * (1/self._FR) #in units: deg/s * pix/deg * s/frame = pixPerFrame 

        self.createOrientationLog()
        
        
        bar = visual.Rect(
                win,
                width = barWidthPix,
                height = barHeightPix,
                fillColor = self.barColor,
                )
        
        totalEpochs = len(self._orientationLog)
        epochNum = 0
        
        trialClock = core.Clock() #this will reset every trial
        for ori in self._orientationLog:
            
            epochNum += 1
            #set initial bar position
            radiansOri = math.radians(ori)
            initialPosition = [-math.cos(radiansOri)*winRadius+winCenter[0], -math.sin(radiansOri)*winRadius+winCenter[1]]
            speedComponents = [math.cos(radiansOri)*pixPerFrame, math.sin(radiansOri)*pixPerFrame];
            
            #move bar by the proper components given the current orientation
            bar.opacity = 0
            bar.pos = initialPosition
            bar.ori = -ori - self._angleOffset#flip for coordinate convention: 0 = east, 90 = north, 180 = west, 270 = south
            

            #show information if necessary
            if self._informationWin[0]:
                self.showInformationText(win, 'Running Moving Bar. Current orientation = ' + \
                                         str(ori) + '\n Epoch ' + str(epochNum) + ' of ' + str(totalEpochs))
            
            
            #pause for inter stimulus interval
            win.color = self.backgroundColor
            for f in range(self._interStimulusIntervalNumFrames):
                win.flip()
                if self.checkQuit():
                    return
                
            
            self._stimulusStartLog.append(trialClock.getTime())
            self.sendTTL()
            self._numberOfEpochsStarted += 1
            #pretime... nothing happens
            for f in range(self._preTimeNumFrames):
                win.flip()
                if self.checkQuit():
                    return
            
            #move the bar during the stim time
            bar.opacity = 1
            for f in range(self._stimTimeNumFrames):
                bar.pos += speedComponents
                bar.draw()
                win.flip()
                if self.checkQuit():
                    return
                    
            #remove bar at the end of the stimulus and wait the post time
            bar.opacity = 0
            for f in range(self._tailTimeNumFrames):
                win.flip()
                if self.checkQuit():
                    return
                
        
            
            self._stimulusEndLog.append(trialClock.getTime())
            self.sendTTL()
            
            
            self._numberOfEpochsCompleted += 1
                
            
        self._completed = 1