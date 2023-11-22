# -*- coding: utf-8 -*-
"""
Created on Thu Jul 15 15:23:17 2021

@author: mrsco
"""

from protocols.protocol import protocol
import random
from psychopy import core, visual, data, event, monitors
import math
import numpy as np
import serial

class CheckerboardReceptiveField(protocol):
    def __init__(self):
        super().__init__()
        self.protocolName = 'CheckerboardReceptiveField'
        self.backgroundColor = [0.0, 0.0, 0.0] #the 'mean' light level that displays between flashes
        self.checkHeight = 1.0 #deg
        self.checkWidth = 1.0 #deg
        self.frameDwell = 1 #update checkerboard every this number of frames
        self.stimulusReps = 3 #times through the stimulus
        self.preTime = 1.0 #s
        self.stimTime = 60.0 #s
        self.tailTime = 5.0 #s
        self.interStimulusInterval = 1.0 #s - wait time between each stimulus. backGround color is displayed during this time
        self.noiseType = 'Binary' #other types not yet implemented... future addition

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



    def generateColorLog(self, numChecks):
        print("Building noise sequence, this may take a while")
        random.seed(self.randomSeed) #reinitialize the random seed

        colorLog = np.empty((self.stimulusReps, int(np.ceil(self._stimTimeNumFrames/self.frameDwell)), numChecks))
        for i in range(self.stimulusReps):
            for j in range(int(np.ceil(self._stimTimeNumFrames/self.frameDwell))):
                for n in range(numChecks):
                    c = int((int(random.random() < 0.5) - 0.5) *2)

                    colorLog[i,j,n] = c #3 dimensional array: d1 = rep number, d2 = flip number for that rep, d3 = check number. Value is the color
        print("Done!")
        return colorLog


    def run(self, win, informationWin):
        '''
        Executes the Checkerboard Receptive Field stimulus
        '''
        self._completed = 0

        self._informationWin = informationWin #tuple, save here so you don't have to pass this as a function parameter every time you use it

        stimMonitor = win.monitor
        pixPerDeg = self.getPixPerDeg(stimMonitor)

        self.getFR(win)
        self._interStimulusIntervalNumFrames = round(self._FR * self.interStimulusInterval)
        self._actualInterStimulusInterval = self._interStimulusIntervalNumFrames * 1/self._FR


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
        colors =[]
        for i in range(len(xCoordinates)):
            for j in range(len(yCoordinates)):
                self.checkCoordinates.append([xCoordinates[i], yCoordinates[j]])


        sizes = [(checkWidthPix, checkHeightPix) for i in range(numChecks)]

        colorLog = self.generateColorLog(numChecks) #3 dimensional numpy array: d1 = rep number, d2 = flip number for that rep, d3 = check number. Value is the color


        noiseField = visual.ElementArrayStim(
            win,
            nElements = numChecks,
            elementMask="None",
            elementTex = None,
            xys = self.checkCoordinates,
            sizes = sizes,
            )


        self.burstTTL(win) #burst to mark onset of the stimulus

        trialClock = core.Clock() #this will reset every trial
        for i in range(self.stimulusReps):

            #show information if necessary
            if self._informationWin[0]:
                self.showInformationText(win, 'Running Checkerboard Receptive Field. Epoch ' + \
                                         str(i+1) + ' of ' + str(self.stimulusReps))

            #pause for inter stimulus interval
            win.color = self.backgroundColor
            for f in range(self._interStimulusIntervalNumFrames):
                win.flip()
                if self.checkQuitOrPause():
                        return


            self._stimulusStartLog.append(trialClock.getTime())
            self.sendTTL()
            self._numberOfEpochsStarted += 1
            #pretime... nothing happens
            for f in range(self._preTimeNumFrames):
                win.flip()
                allKeys = event.getKeys() #check if user wants to quit early
                if self.checkQuitOrPause():
                        return

            #stim time

            #decrease baudrate for speed during frame flips
            if self.writeTTL == 'Pulse':
                self._portObj.baudrate = 1000000

            for f in range(self._stimTimeNumFrames):
                flipNum = f//self.frameDwell
                if flipNum == f/self.frameDwell:
                    colors = [[color, color, color] for color in colorLog[i, flipNum]]
                    noiseField.colors = colors

                noiseField.draw()
                win.flip()
                self.sendTTL()  #write ttl for every frame flip for this stimulus
                if self.checkQuitOrPause():
                        return

            #return baudrate to high value
            if self.writeTTL == 'Pulse':
                self._portObj.baudrate = 4000000

            #tail time
            for f in range(self._tailTimeNumFrames):
                win.flip()
                if self.checkQuitOrPause():
                        return


            self._stimulusEndLog.append(trialClock.getTime())
            self.sendTTL()

            self._numberOfEpochsCompleted += 1


        self._completed = 1
