# -*- coding: utf-8 -*-
"""
Created on Mon Aug  2 15:46:55 2021

@author: mrsco
"""
from protocols.protocol import protocol
from psychopy import core, visual, data, event, monitors
import serial, random, numpy, time

class PupilCalibration(protocol):
    def __init__(self):
        super().__init__()
        self.protocolName = 'PupilCalibration' #the pupil calibration is a unique stimulus used for eye tracking experiments on a mouse behavior rig - as in https://elifesciences.org/articles/81780 . It requires the user to dynamically swing a camera between two locations and snap pictures at each. It also modulates the light level of the screen background level during this time in order to capture values across many pupil sizes.
        self.numberOfLightLevels = 5 #number of different light levels to test across. The total number of epochs for this stimulus is equal to the number of light levels multiplied by the repetitions per light level.
        self.repititionsPerLightLevel = 5 #the number of times each light level is repeated.The total number of epochs for this stimulus is equal to the number of light levels multiplied by the repetitions per light level.
        self.angle = 11.4 #degrees - the angle that the camera is rotated by between successive pictures... This was calculated as 11.4 degrees for the Dunn Lab behavior rig as of January 12, 2022.

        self.preTime = 1.0 #seconds - unused for this stimulus
        self.stimTime = 1.0 #seconds - unused for this stimulus
        self.tailTime = 1.0 #seconds - unused for this stimulus
                
        self._versionNumber = 1.2 #Version of the stimulus -
                                        #1.1 - this attribute didn't exist yet. There was a bug with win.flip() where the screen color wouldn't change
                                        #until after the second screen flip. This means that in version 1.0 the light level log is off by an index of 1.0
                                        #relative to what the actual stimulus was. In other words, the true self._lightLevelLog that was used in the experiment
                                        #was equal to [-1] + self._lightLevelLog[0:-1] (noninclusive of the last value). First value was always -1 b/c the stimulus
                                        #screen started at this value by default
                                        
                                        #1.2 - 1/17/2022 - Now the self._lightLevelLog reflects the actual stimulus that was used in the experiment. (added a double win.flip)
                                        # during the stimulus loop
        
    def estimateTime(self):
        '''
        Estimate the total amount of time that this protocol will take to run
        given the current parameters
        
        Value is stored as total time in seconds in the property 'self.estimatedTime'
        which is initialized by the protocol superclass.
        
        returns: estimated time in seconds
        '''
        timePerCalibration = 7 #estimated time it takes per calibration value
        numberOfCalibrations = self.numberOfLightLevels*self.repititionsPerLightLevel*2
        self._estimatedTime = timePerCalibration * numberOfCalibrations #return estimated time for the total stimulus in seconds
        
        return self._estimatedTime
      
    
    
    def createLightLevelLog(self):
        '''
        Generate a random sequence of orientations given the desired orientations
        
        Desired orientations are specified as a list in self.orientations
        
        creates self.orientationLog, a list, which specifies the orienation 
        to use for each epoch
        '''
        lightLevels = list(numpy.linspace(-1, 1, self.numberOfLightLevels))
        self._lightLevelLog = []
        random.seed(self.randomSeed) #reinitialize the random seed
        
        for n in range(self.repititionsPerLightLevel):
            self._lightLevelLog += random.sample(lightLevels, len(lightLevels))
            
    
    def run(self, win, informationWin):
        '''
        Executes the PupilCalibration stimulus
        '''
        self._completed = 0 #started but not completed
        
        self._informationWin = informationWin #tuple, save here so you don't have to pass this as a function parameter every time you use it
        
        self.getFR(win)
        
                
        #Pause for keystroke if the user wants to manually initiate
        if self.userInitiated:
            self.showInformationText(win, 'Stimulus Information: Pupil Calibration \nPress any key to begin')
            event.waitKeys() #wait for key press  
        
                
        self.createLightLevelLog()

        totalEpochs = len(self._lightLevelLog)
        epochNum = 0
        trialClock = core.Clock() #this will reset every trial
        
        for level in self._lightLevelLog:
            win.color = [level, level, level];
            epochNum += 1
            win.flip()
            win.flip()

            #LEFT SIDE SNAP FIRST
            if self._informationWin[0]:
                self.showInformationText(win, 'Move the camera to the LEFT, then press enter ' + \
                                          '\n Epoch ' + str(epochNum) + ' of ' + str(totalEpochs))
            
            self._numberOfEpochsStarted += 1
            self._stimulusStartLog.append(trialClock.getTime())
            
            event.waitKeys() #wait for key press to signal moving on to the next epoch
            self.sendTTL() #mark left side snap
            time.sleep(0.5)
            self.sendTTL()
            self.checkQuitOrPause()
            
            #RIGHT SIDE SNAP SECOND
            if self._informationWin[0]:
                self.showInformationText(win, 'Move the camera to the RIGHT, then press enter ' + \
                                          '\n Epoch ' + str(epochNum) + ' of ' + str(totalEpochs))
           

            event.waitKeys() #wait for key press to signal moving on to the next epoch
            self.sendTTL() #mark right side snap
            time.sleep(0.5)
            self.sendTTL()
            
            self.checkQuitOrPause()
            self._stimulusEndLog.append(trialClock.getTime())
            self._numberOfEpochsCompleted += 1
                
        
        #mark primary and secondary LEDs
        self.showInformationText(win, 'ALMOST DONE \n Move the camera to the RECORDING POSITION and turn on the TOP LED, then press enter')
        event.waitKeys() #wait for key press to signal moving on to the next epoch
        self.sendTTL() #mark right side snap
        time.sleep(0.5)
        self.sendTTL()
        
        self.showInformationText(win, 'ALMOST DONE \n Move the camera to the RECORDING POSITION and turn on the SIDE LED, then press enter')
        event.waitKeys() #wait for key press to signal moving on to the next epoch
        self.sendTTL() #mark right side snap
        time.sleep(0.5)
        self.sendTTL()
            
        self._completed = 1