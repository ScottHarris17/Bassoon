# -*- coding: utf-8 -*-
"""
Created on Sat Apr 15 17:39:25 2023

@author: mrsco
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Aug  2 15:46:55 2021

@author: mrsco
"""
from protocols.protocol import protocol
from psychopy import core, visual, data, event, monitors
import serial, random, numpy, time
from psychopy.hardware import keyboard

class SnellenShapes(protocol):
    
    def __init__(self):
        super().__init__()
        self.protocolName = 'SnellenShapes'
        self.numberOfOptotypes = 10
        self.startingLevel = 5 #0 is the smallest optotype               
       
        self.textColor = [-1.0, -1.0, -1.0]
        self.backgroundColor = [1.0, 1.0, 1.0]
        
        self.smallestOptotypeRadius_degrees = 0.2
        self.largestOptotypeRadius_degrees = 4
        
        self.preTime = 1.0 #s - unused for this stimulus
        self.stimTime = 1.0 #s - unused for this stimulus
        self.tailTime = 1.0 #s - unused for this stimulus
        
    def estimateTime(self):
        '''
        Estimate the total amount of time that this protocol will take to run
        given the current parameters
        
        Value is stored as total time in seconds in the property 'self.estimatedTime'
        which is initialized by the protocol superclass.
        
        returns: estimated time in seconds
        '''
        self._estimatedTime = 120 #return estimated time for the total stimulus in seconds
        
        return self._estimatedTime
      
    def calculateOptotypeRadii_pix(self):
        '''
        Calculates the radius of each optotype in pixels, given the minimmum and
        maximum radii and the number of optotype levels
        '''
        minRadius_pix = self.smallestOptotypeRadius_degrees*self.pixPerDegree
        maxRadius_pix = self.largestOptotypeRadius_degrees*self.pixPerDegree
        allRadii_pix = numpy.linspace(minRadius_pix, maxRadius_pix, num = self.numberOfOptotypes)
        return allRadii_pix
    
    def procedureAlgo(self, score, currentLevel, epochNum):
        if epochNum == 10:
            testComplete = 1
        else:
            testComplete = 0
        
        nextLevel = currentLevel + score
        
        if nextLevel > len(self.allRadii_pix)-1 or nextLevel < 0:
            testComplete = 1
            
        return testComplete, nextLevel
        
        
    def run(self, win, informationWin):
        '''
        Executes the SnellenShapes stimulus
        '''
        self._completed = 0 #started but not completed
        
        self._informationWin = informationWin #tuple, save here so you don't have to pass this as a function parameter every time you use it
        
        self.getFR(win)
        
        stimMonitor = win.monitor
        
        self.pixPerDegree = self.getPixPerDeg(stimMonitor)
        
        self.allRadii_pix = self.calculateOptotypeRadii_pix()
        
        #Pause for keystroke if the user wants to manually initiate
        if self.userInitiated:
            self.showInformationText(win, 'Stimulus Information: Snellen Shapes \nPress any key to begin')
            event.waitKeys() #wait for key press  
        
        
        instructions = 'Snellen Shape Test for Visual Acuity: \nPress "C" for Circle and "S" for square \n\nPress any key to begin'
        self.showInformationText(win, instructions)
        event.waitKeys() #wait for key press
        
        kb = keyboard.Keyboard()
        
        win.color = self.backgroundColor
        win.flip()
        win.flip()
        
        #initialize the circle
        optotypeCircle = visual.Circle(
            win = win,
            units = 'pix',
            lineColor = self.textColor,
            lineWidth = 2,
            fillColor = self.backgroundColor
            )
        
        #initialize the square
        optotypeSquare = visual.Rect(
            win = win,
            units = 'pix',
            lineColor = self.textColor,
            lineWidth = 2,
            fillColor = self.backgroundColor
            )
        
        random.seed(self.randomSeed) #reinitialize the random seed
        
        epochNum = 0
        testComplete = False
        trialClock = core.Clock() #this will reset every trial
        nextOptotypeLevel = self.startingLevel
        
        while not testComplete:
            currentOptotypeLevel = nextOptotypeLevel
            currentRadius = self.allRadii_pix[currentOptotypeLevel]
            
            isCircle = random.random() > 0.5 #randomly choose the optotype
            
            if isCircle:
                optotypeCircle.radius = currentRadius
                optotypeCircle.draw()
            else:
                optotypeSquare.width = currentRadius
                optotypeSquare.height = currentRadius
                optotypeSquare.draw()
                
            win.flip()
            keypress = kb.waitKeys(keyList = ['c', 's', 'q'])
            thisKey = keypress[0].name
            
            if thisKey == 'q':
                break
            
            if (thisKey == 'c' and isCircle) or (thisKey =='s' and not isCircle):
                score = -1
            else:
                score = 1
            
            (testComplete, nextOptotypeLevel) = self.procedureAlgo(score, currentOptotypeLevel, epochNum)
            epochNum += 1
            
        
        print('Your optotype level is', currentOptotypeLevel, 'out of', self.numberOfOptotypes)
        self._completed = 1

        