# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10 13:30:40 2024

@author: david
"""

from protocols.protocol import protocol
from psychopy import core, visual, data, event, monitors
import numpy
import serial

class Flicker(protocol):
    def __init__(self):
        super().__init__()
        self.protocolName = 'Flicker' #The flicker protocol alternates between a full field flash on the screen and the background color for a specified amount of time
        self.flashIntensity = [1.0, 1.0, 1.0] #intensity of the screen (in RGB) during the flash. -1.0 equates to 0 and 1.0 equates to 255 for 8 bit colors.
        self.backgroundColor = [-1.0, -1.0, -1.0] #background color of the screen before/after the flash  (in RGB). -1.0 equates to 0 and 1.0 equates to 255 for 8 bit colors.
        self.stimulusReps = 1 #number of repetitions
        self.preTime = 1.0 #seconds - the amount of time before the flash on each epoch, during which the background is shown
        self.stimTime = 5.0 #seconds - the amount of time that the flash lasts for
        self.tailTime = 1.0 #seconds - the amount of time after the flash on each epoch, during which the background is shown
        self.interStimulusInterval = 1.0 #seconds - the wait time between each epoch. The background color is displayed during this time.
        self.flickerInterval = 1.0 #seconds - the amount of time that each flicker lasts       
        self.flickerType = 'custom' #Determines what happens during the "off" cycle of the flicker. "negative" presents the negative rgb value of the "flash intensity", 'background' presents the background color, 'custom' presents a custom color - default is 'custom' when the string input does not match a known case
        self.customOffColor = [0.0, 0.0, 0.0] #Sets the off color of the flicker cycle, BUT only is used if the flicker type is set to "custom" 
        
        
    def internalValidation(self):
             '''
             Validates the properties. This is called when the user updates the protocol's properties. It is directly called by the validatePropertyValues() method in the protocol super class
         
             -------
             Returns:
                 tf - bool value, true if validations are passed, false if they are not
                 errorMessage - string, message to be displayed in validations are not passed
         
             '''
             tf = True
             errorMessage = []
             possibleFlickerTypes = ['negative', 'custom', 'background']
             if self.flickerType not in possibleFlickerTypes:
                 print(self.flickerType)
                 tf = False
                 errorMessage.append('Invalid Flicker Type. Choose between \'negative\', \'custom\', and \'background\'')
            
             tf, colorErrorMessages = self.validateColorInput()
             errorMessage += colorErrorMessages
             
             return tf, errorMessage
         
            
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
      

            
    def run(self, win, informationWin):
        '''
        Executes the Flicker stimulus
        '''

        self._completed = 0 #started but not completed
        
        self._informationWin = informationWin #tuple, save here so you don't have to pass this as a function parameter every time you use it
        
        #self.switch is a list that contains the color that the screen should take when the flicker is on its "off" cycle
        if self.flickerType == 'negative':
            self.offColor = [-rgb for rgb in self.flashIntensity]
        elif self.flickerType == 'background':
            self.offColor = self.backgroundColor
        else: #'custom'
            self.offColor = self.customOffColor
             
        
        self.getFR(win)
        self._interStimulusIntervalNumFrames = round(self._FR * self.interStimulusInterval)
        self._actualInterStimulusInterval = self._interStimulusIntervalNumFrames * 1/self._FR
        
        self._flickerNumFrames = round(self._FR * self.flickerInterval)
        self._actualFlickerInterval = self._flickerNumFrames / self._FR
        
        #Pause for keystroke if the user wants to manually initiate
        if self.userInitiated:
            self.showInformationText(win, 'Stimulus Information: Flicker\nPress any key to begin')
            event.waitKeys() #wait for key press  
        
        epochNum = 0
        trialClock = core.Clock() #this will reset every trial
        
        self.flickerCount = self._stimTimeNumFrames / self._flickerNumFrames
        self.roundedFlickerCount = round(self.flickerCount)
        
        
        for stim in range(self.stimulusReps):
            epochNum += 1
        
            #show information if necessary
            if self._informationWin[0]:
                self.showInformationText(win, 'Running Flicker\n Epoch ' + str(epochNum) + ' of ' + str(self.stimulusReps))
            
            #pause for inter stimulus interval
            win.color = self.backgroundColor
            for f in range(self._interStimulusIntervalNumFrames):
                win.flip()
                if self.checkQuitOrPause():
                    return
                    
            #pretime... nothing happens
            self._stimulusStartLog.append(trialClock.getTime())
            self.sendTTL()
            self._numberOfEpochsStarted += 1
            for f in range(self._preTimeNumFrames):
                win.flip()
                if self.checkQuitOrPause():
                    return
            

            #stim time - flicker
            count = self._flickerNumFrames
            switch = True
            for f in range(self._stimTimeNumFrames):
                if count == self._flickerNumFrames:
                    if switch:
                        win.color = self.flashIntensity
                        switch = False
                    else:
                        win.color = self.offColor
                        switch = True
                    count = 0
                
                count += 1
                win.flip()
                if self.checkQuitOrPause():
                    return

            #tail time
            win.color = self.backgroundColor
            for f in range(self._tailTimeNumFrames):
                win.flip()
                if self.checkQuitOrPause():
                    return
        
            

                
            self._stimulusEndLog.append(trialClock.getTime())
            self.sendTTL()
            
            self._numberOfEpochsCompleted += 1
                
        self._completed = 1