# -*- coding: utf-8 -*-
"""
Created on Sun Oct 29 20:12:51 2023

@author: mrsco
"""

from protocols.protocol import protocol
from psychopy import core, visual, data, event, monitors
import serial, random, math

class FlashGrid(protocol):
    def __init__(self):
        super().__init__()
        self.protocolName = 'FlashGrid'
        self.flashColor = [1.0, 1.0, 1.0]
        self.flashIntensity = 0.5 #multiplied by the color
        self.checkHeight = 3.0 #degrees
        self.checkWidth = 3.0 #degrees
        self.estimatedNumberOfChecks = 40 #this parameter is not really important. It is only used for the estimated time function because it is hard to calculate the true grid size prior to running the stimulus 
        self.flashDuration = 1.0 #seconds
        self.repsPerCheck = 5 #repetitions per flash, on each of self.stimulusReps
        self.interFlashInterval = 1.0 #seconds
        self.backgroundColor = [0.0, 0.0, 0.0]
        self.stimulusReps = 3 #number of times the full stimulus is repeated
        self.preTime = 1.0 #s
        self.stimTime = 0.0 #s - placeholder/dummy variable for this experiment b/c it is required by the getFR method in protocol.py
        self.tailTime = 1.0 #s
        self.interStimulusInterval = 1.0 #s - wait time between each stimulus. backGround color is displayed during this time
        self._angleOffset = 0.0 # reassigned by the experiment in most cases

    def estimateTime(self):
        '''
        Estimate the total amount of time that this protocol will take to run
        given the current parameters.
        
        Unfortunately, it is nontrivial to determine how many checks will be on
        the screen before retreiving the window information from the experiment
        (which will not have been initialized at the time that this function runs).
        
        Therefore, assume number of checks based on self.estimatedNumberOfChecks
        parameter.

        Value is stored as total time in seconds in the property 'self.estimatedTime'
        which is initialized by the protocol superclass.

        returns: estimated time in seconds
        '''
        
        timePerEpoch = self.preTime + self.estimatedNumberOfChecks * (self.flashDuration + self.interFlashInterval) * self.repsPerCheck + self.tailTime
        numberOfEpochs = self.stimulusReps
        self._estimatedTime = timePerEpoch * numberOfEpochs #return estimated time for the total stimulus in seconds
        return self._estimatedTime

    def setFlashSequence(self, numChecks):
        '''
        Set the sequence of flashes for each check in the grid.
        
        The flash sequence is a list of lists. The outer list has n elements, 
        equal to the number of stimulus repetitions (i.e. epochs). The inner list
        has m elements, equal to the total number of flashes per epoch
        (i.e., number of checks * repsPerCheck).
        '''
        random.seed(self.randomSeed) #reinitialize the random seed
        self._flashSequence = [] #initialize, this will end up being a list of lists
        for i in range(self.stimulusReps):
            thisEpoch = []
            for j in range(self.repsPerCheck):
                thisEpoch += [random.sample(range(numChecks), numChecks)]
            
            self._flashSequence += thisEpoch


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
        
        self._flashDurationNumFrames = round(self._FR * self.flashDuration)
        self._actualFlashDuration = self._flashDurationNumFrames * 1/self._FR
        
        self._interFlashIntervalNumFrames = round(self._FR * self.interFlashInterval)
        self._actualInterFlashInterval = self._interFlashIntervalNumFrames * 1/self._FR
        

        #Pause for keystroke if the user wants to manually initiate
        if self.userInitiated:
            self.showInformationText(win, 'Stimulus Information: Flash Family \nPress any key to begin')
            event.waitKeys() #wait for key press

        winWidthPix = win.size[0]
        winHeightPix = win.size[1]

        checkWidthPix = int(self.checkWidth*pixPerDeg) #maybe a slight rounding error here by using int
        checkHeightPix = int(self.checkHeight*pixPerDeg)

        #specify the x and y center coordinates for each check
        xCoordinates = [x - win.size[0]/2 for x in range(-checkWidthPix,win.size[0]+checkWidthPix,checkWidthPix)]
        yCoordinates = [y - win.size[1]/2 for y in range(-checkHeightPix,win.size[1]+checkHeightPix,checkHeightPix)]
        numChecks = len(xCoordinates)*len(yCoordinates)

        self.checkCoordinates = []
        for i in range(len(xCoordinates)):
            for j in range(len(yCoordinates)):
                self.checkCoordinates.append([xCoordinates[i], yCoordinates[j]])

        sizes = [(checkWidthPix, checkHeightPix) for i in range(numChecks)]
        colors = [self.backgroundColor for i in range(numChecks)]
        
        flashField = visual.ElementArrayStim(
            win,
            nElements = numChecks,
            elementMask="None",
            elementTex = None,
            xys = self.checkCoordinates,
            sizes = sizes,
            colors = colors
            )
        
        self.setFlashSequence(numChecks)
        
        self.burstTTL(win) #burst to mark onset of the stimulus

        trialClock = core.Clock() #this will reset every trial
        
        epochNum = 0
        flashColor = [c * self.flashIntensity for c in self.flashColor]
        #stimulus loop
        for sequence in self._flashSequence: #looping through the outer list
            epochNum += 1
            
            #show information if necessary
            if self._informationWin[0]:
                self.showInformationText(win, 'Running Checkerboard Receptive Field. Epoch ' + \
                                         str(i+1) + ' of ' + str(self.stimulusReps))

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
                allKeys = event.getKeys() #check if user wants to quit early
                if self.checkQuit():
                        return

            #there are two stimulus options. If the user is writing TTL, then it is sent at the onset of each individual flash
            if self.writeTTL: 
                #decrease baudrate for speed during frame flips
                if self.writeTTL == 'Pulse':
                    self._portObj.baudrate = 1000000
        
            #stim time
            for check in sequence:
                
                flashField.colors[check] = flashColor #set just the check of interest to have full opacity
                for f in range(self._flashDurationNumFrames):
                    flashField.draw()
                    win.flip()
                    if f == 0 and self.writeTTL:
                        self.sendTTL()  #write ttl at the onset of every flash
                    
                    if self.checkQuit():
                        return
            
                flashField.colors = colors #reset opacities to all zero
                
                #wait the interFlashInterval time
                for f in range(self._interFlashIntervalNumFrames):
                    win.flip()
                    if self.checkQuit():
                        return

            #return baudrate to high value
            if self.writeTTL == 'Pulse':
                self._portObj.baudrate = 4000000


            #tail time
            for f in range(self._tailTimeNumFrames):
                win.flip()
                if self.checkQuit():
                        return


            self._stimulusEndLog.append(trialClock.getTime())
            self.sendTTL()

            self._numberOfEpochsCompleted += 1

        self._completed = 1