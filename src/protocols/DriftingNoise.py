# -*- coding: utf-8 -*-
"""
Created on Sat Oct 14 00:12:44 2023

Noise pattern moves in random directions distributed within some window

@author: mrsco
"""
from protocols.protocol import protocol
from psychopy import core, visual, data, event, monitors
import serial, random, math

class DriftingNoise(protocol):
    def __init__(self):
        super().__init__()
        self.protocolName = 'DriftingNoise' #During drifting noise, a noise pattern drifts linearly across the window in a specified range of directions
        self.noiseType = 'Binary' #The type of noise pattern to use (only binary is available for now)
        self.patternColor = [1.0, 1.0, 1.0] #color of the pattern in RGB, where -1 equates to 0 and 1 equates to 255 in an 8 bit color code.
        self.patternContrast = 1.0 #The contrast of the pattern (multiplied by the pattern color).
        self.orientations = sum([[g for g in range(45, 136, 5)], [m for m in range(225, 316, 5)]], []) #degrees - directions across the screen that the stimulus will drift. The stimulus will cycle through each orientation on every repetition, but the order is pseudorandom. 
        self.speed = 10.0 #degrees per second - the speed at which the noise pattern drifts
        self.checkSize = 0.5 #degrees - number of visual degrees that 1 noise check should subtend
        self.backgroundColor = [0.0, 0.0, 0.0] #background color of the screen before/after the flash  (in RGB). -1.0 equates to 0 and 1.0 equates to 255 for 8 bit colors.
        self.meanIntensity = 0.0 #Mean intensity of the noise. This must be 0 if the pattern contrast is 1.0. For lower contrasts, the mean intensity can be changed.
        self.stimulusReps = 5 #number of repetitions of the stimulus. Each repition includes one pseudorandom cycle through the orientations. Thus, the number of epochs is equal to the number of orientations times the number of stimulus reps.
        self.preTime = 0.5 #seconds - during the pretime, the noise pattern is visible, but not moving.
        self.stimTime = 3.0 #seconds - during the stimtime, the noise pattern is visible and drifting across the screen at the specified speed.
        self.tailTime = 0.0 #seconds - during the tailtime, the noise pattern is visible, but not moving. It is the same as the pretime, but happens after the stim time instead of before
        self.interStimulusInterval = 0.5 #seconds - the wait time between each epoch. The background color is displayed during this time.
        self._angleOffset = 0.0 # reassigned by the experiment in most cases

    def estimateTime(self):
        '''
        Estimate the total amount of time that this protocol will take to run
        given the current parameters

        Value is stored as total time in seconds in the property 'self.estimatedTime'
        which is initialized by the protocol superclass.

        returns: estimated time in seconds
        '''
        timePerEpoch = self.preTime + self.stimTime + self.tailTime + self.interStimulusInterval
        numberOfEpochs = self.stimulusReps * len(self.orientations)
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
        Executes the OKR Discrimination stimulus
        '''

        self._completed = 0 #started but not completed

        self._informationWin = informationWin #tuple, save here so you don't have to pass this as a function parameter every time you use it


        self.getFR(win)
        self._interStimulusIntervalNumFrames = round(self._FR * self.interStimulusInterval)
        self._actualInterStimulusInterval = self._interStimulusIntervalNumFrames * 1/self._FR

        stimMonitor = win.monitor
        pixPerDeg = self.getPixPerDeg(stimMonitor)

        #Pause for keystroke if the user wants to manually initiate
        if self.userInitiated:
            self.showInformationText(win, 'Stimulus Information: OKR Discrimination\nPress any key to begin')
            event.waitKeys() #wait for key press
        
        checkSizePix = self.checkSize * pixPerDeg
        
        pattern = visual.NoiseStim(
            win, name = 'noise',
            size = (win.size[0]*2, win.size[1]*2),
            noiseType= self.noiseType,
            noiseElementSize = checkSizePix, #pixels
            contrast = self.patternContrast,
            color = self.patternColor
            )


        #The cover rectangle is drawn on top of the primary pattern. It is used
        #to change the mean intensity of the pattern when the user desires.
        #If the mean intensity is set to 0, then the cover rectangle is still
        #drawn but with an opacity of 0
        coverRectangle = visual.Rect(
            win,
            size = (win.size[0]*2, win.size[1]*2),
            opacity = 0
            )

        if self.meanIntensity > 0:
            coverRectangle.fillColor = [1, 1, 1]
            coverRectangle.opacity = self.meanIntensity
        elif self.meanIntensity < 0:
            coverRectangle.fillColor = [-1, -1, -1]
            coverRectangle.opacity = -1*self.meanIntensity
            
        cyclesPerPix = pattern.sf[1]
        self._numCyclesToShiftByFrame = self.speed*pixPerDeg*cyclesPerPix*(1/self._FR) #using y coordinate of sf

        self.createOrientationLog()

        totalEpochs = len(self._orientationLog)
        epochNum = 0
        trialClock = core.Clock() #this will reset every trial

        self._totalFrames = (self._interStimulusIntervalNumFrames+self._preTimeNumFrames+self._stimTimeNumFrames+self._tailTimeNumFrames)*self.stimulusReps
        
        #stimulus loop
        for ori in self._orientationLog:
            pattern.ori = -ori + 37 - self._angleOffset #add 37 b/c for some reason binary noise phase modulates along this direction... flip for coordinate convention: 0 = east, 90 = north, 180 = west, 270 = south
            epochNum += 1
            print (ori)
            #show information if necessary
            if self._informationWin[0]:
                self.showInformationText(win, 'Running OKR Discrimination. Current orientation = ' + \
                                         str(ori) + '\n Epoch ' + str(epochNum) + ' of ' + str(totalEpochs))


            #pause for inter stimulus interval
            win.color = self.backgroundColor
            for f in range(self._interStimulusIntervalNumFrames):
                win.flip()
                if self.checkQuitOrPause():
                    return

            #pretime... stationary pattern
            self._stimulusStartLog.append(trialClock.getTime())
            self.sendTTL()
            self._numberOfEpochsStarted += 1
            for f in range(self._preTimeNumFrames):
                pattern.draw()
                coverRectangle.draw()
                win.flip()
                if self.checkQuitOrPause():
                    return
            
            
            #stim time - drifting pattern
            for f in range(self._stimTimeNumFrames):
                pattern.phase += self._numCyclesToShiftByFrame
                pattern.draw()
                coverRectangle.draw()
                win.flip()
                if self.checkQuitOrPause():
                    return

            #tail time - stationary pattern
            for f in range(self._tailTimeNumFrames):
                pattern.draw()
                coverRectangle.draw()
                win.flip()
                if self.checkQuitOrPause():
                    return

            self._stimulusEndLog.append(trialClock.getTime())
            self.sendTTL()
            win.flip();win.flip() #two flips to allow for a pause for TTL writing

            self._numberOfEpochsCompleted += 1


        self._completed = 1
