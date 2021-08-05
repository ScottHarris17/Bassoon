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
        self.protocolName = 'PupilCalibration'
        self.numberOfLightLevels = 5
        self.repititionsPerLightLevel = 5
        self.angle = 10 #degrees - angkle that the camera is rotated by

        self.preTime = 1.0 #s - unimportant for this stimulus
        self.stimTime = 1.0 #s - unimportant for this stimulus
        self.tailTime = 1.0 #s - unimportant for this stimulus
                
        
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
        Executes the MovingBar stimulus
        '''
        self._completed = 0 #started but not completed
        
        self._informationWin = informationWin #tuple, save here so you don't have to pass this as a function parameter every time you use it
        
        self.getFR(win)
        
        stimMonitor = win.monitor
                
        #Pause for keystroke if the user wants to manually initiate
        if self.userInitiated:
            self.showInformationText(win, 'Stimulus Information: Pupil Calibration \nPress any key to begin')
            event.waitKeys() #wait for key press  
        
                
        self.createLightLevelLog()

        totalEpochs = len(self._lightLevelLog)
        epochNum = 0
        trialClock = core.Clock() #this will reset every trial
        
        for level in self._lightLevelLog:
            print(level)
            win.color = [level, level, level];
            epochNum += 1
            win.flip()

            #LEFT SIDE SNAP FIRST
            if self._informationWin[0]:
                self.showInformationText(win, 'Move the camera to the LEFT, then press enter ' + \
                                          '\n Epoch ' + str(epochNum) + ' of ' + str(totalEpochs))
            
            self._numberOfEpochsStarted += 1
            self._stimulusStartLog.append(trialClock.getTime())
            event.waitKeys() #wait for key press to signal moving on to the next epoch
            self.sendTTL() #mark left side snap
            self.checkQuit
            
            #RIGHT SIDE SNAP SECOND
            if self._informationWin[0]:
                self.showInformationText(win, 'Move the camera to the RIGHT, then press enter ' + \
                                          '\n Epoch ' + str(epochNum) + ' of ' + str(totalEpochs))
            event.waitKeys() #wait for key press to signal moving on to the next epoch
            self.sendTTL() #mark right side snap
            self.checkQuit
            self._stimulusEndLog.append(trialClock.getTime())
            self._numberOfEpochsCompleted += 1
                
            
        self._completed = 1