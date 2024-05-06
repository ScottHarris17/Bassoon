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
        
        
    def internalValidation(self, tf = True, errorMessage = ''):
         '''
         Validates the properties. This is called when the user updates the protocol's properties. It is directly called by the validatePropertyValues() method in the protocol super class
     
         -------
         Returns:
             tf - bool value, true if validations are passed, false if they are not
             errorMessage - string, message to be displayed in validations are not passed
     
         '''
         if self.stimTime != 0:
             tf = True
             errorMessage = ''
             print('Validations were passed, but stimTime must be 0 and was forced back to this value (it is a dummy variable for this stimulus).')
             self.stimTime = 0.0
             
         return tf, errorMessage
     
        
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
    
    def secondsToMinutesAndSeconds(self, seconds):
        '''
        Given a number specifying a time in seconds, this function returns the
        equivalent number of minutes and seconds

        Parameters
        ----------
        seconds : Number. Specifies time in seconds

        Returns
        -------
        roundedMinutes : integer of total minutes
        remainingSeconds: integer of remaining seconds in addition to roundedMinutes
        '''
        minutes = seconds/60
        rounded_minutes = math.floor(minutes)
        remainingSeconds = int((minutes-rounded_minutes)*60)

        return rounded_minutes, remainingSeconds



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
        
        self._interFlashIntervalNumFrames = round(self._FR * self.interFlashInterval) + 1 #add 1 frame because it is helpful to have at least a brief pause between stimuli for the TTL pattern
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

        self._checkCoordinates = []
        for i in range(len(xCoordinates)):
            for j in range(len(yCoordinates)):
                self._checkCoordinates.append([xCoordinates[i], yCoordinates[j]])

        sizes = [(checkWidthPix, checkHeightPix) for i in range(numChecks)]
        colors = [self.backgroundColor for i in range(numChecks)]
        
        flashField = visual.ElementArrayStim(
            win,
            nElements = numChecks,
            elementMask="None",
            elementTex = None,
            xys = self._checkCoordinates,
            sizes = sizes,
            colors = colors
            )
        
        self.setFlashSequence(numChecks)
        
        self.estimatedNumberOfChecks = numChecks
        totalS = self.estimateTime()
        m, s = self.secondsToMinutesAndSeconds(totalS)
        print("--> Time Estimate Update: There are " + str(numChecks) + " checks to present. \
              this stimulus is now estimated to take " + str(m) + " minutes and " \
                  + str(s) + " seconds")
        
        self.burstTTL(win) #burst to mark onset of the stimulus for pulse mode only

        trialClock = core.Clock() #this will reset every trial
        
        epochNum = 0
        flashColor = [c * self.flashIntensity for c in self.flashColor]
        #stimulus loop
        for sequence in self._flashSequence: #looping through the outer list
            epochNum += 1
            
            #show information if necessary
            if self._informationWin[0]:
                self.showInformationText(win, 'Running Flash Grid. Epoch ' + \
                                         str(epochNum) + ' of ' + str(self.stimulusReps))

            #pause for inter stimulus interval
            win.color = self.backgroundColor
            for f in range(self._interStimulusIntervalNumFrames):
                win.flip()
                if self.checkQuitOrPause():
                        return


            self._stimulusStartLog.append(trialClock.getTime())
            self._numberOfEpochsStarted += 1
            #pretime... nothing happens
            for f in range(self._preTimeNumFrames):
                win.flip()
                allKeys = event.getKeys() #check if user wants to quit early
                if self.checkQuitOrPause():
                        return

            #decrease baudrate for speed during frame flips
            if self.writeTTL == 'Pulse':
                self._portObj.baudrate = 1000000
        
            #stim time
            for check in sequence:
                
                #use this weird work around to change flash color
                #   because there is a problem with indexing directly to flashField.colors on some computers
                cs = flashField.colors
                cs[check, :] = flashColor
                flashField.colors = cs
                for f in range(self._flashDurationNumFrames):
                    flashField.draw()
                    win.flip()
                    if f == 0:
                        self.sendTTL()  #write ttl at the onset of every flash
                    
                    if self.checkQuitOrPause():
                        return
            
                flashField.colors = colors #reset opacities to all zero
                self.sendTTL()
                
                #wait the interFlashInterval time
                for f in range(self._interFlashIntervalNumFrames):
                    win.flip()
                    if self.checkQuitOrPause():
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
            
            self._numberOfEpochsCompleted += 1

        self._completed = 1
