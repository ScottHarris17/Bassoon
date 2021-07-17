# -*- coding: utf-8 -*-
"""
Created on Wed Jul  7 18:48:52 2021

@author: mrsco
"""
from psychopy import core, visual, gui, data, event, monitors
from psychopy.tools.filetools import fromFile, toFile
import numpy, random, math
import copy
import serial

class experiment():
    def __init__(self):
        self.protocolList = []
        self.activated = False
        
        self.allowGUI = True
        self.screen = 0
        self.fullscr = False
        self.backgroundColor = [-1, -1, -1]
        self.units = 'pix'
        self.allowStencil = True
        self.activated = False
        self.stimMonitor = 'uranusPrimary'
        
        self.useInformationMonitor = False
        self.informationMonitor = 'uranusPrimary'
        self.informationWin = None
        self.informationScreen = 0
        
        self.loggedStimuli = []
    def addProtocol(self, newProtocol):
        self.protocolList.append((newProtocol.protocolName, newProtocol))
        
    
    def activate(self):
        self.win = visual.Window(
                    allowGUI=self.allowGUI, 
                    monitor = self.stimMonitor, 
                    screen = self.screen, 
                    fullscr = self.fullscr,
                    color = self.backgroundColor,
                    units = self.units,
                    allowStencil = self.allowStencil)
        
        #if the user would like to uise a second screen to display stimulus information then initialize that screen here
        #the flips to this second window must be called in the stimulus protocol itself
        if self.useInformationMonitor:
            self.informationWin = visual.Window(
                        allowGUI = self.allowGUI,
                        monitor = self.informationMonitor,
                        screen = self.informationScreen,
                        color = self.backgroundColor, 
                        fullscr = False,
                        units = self.units,
                        )
            
        
        self.activated = True
        
        for p in self.protocolList:
            p = p[1] #the protocol object is the second one in the tuple
            p.run(self.win, (self.useInformationMonitor, self.informationWin)) #send informationMonitor information as a tuple: bool (whether to use), window information
            
            #write down properties from previous stimulus
            protocolProperties = vars(p)
            self.loggedStimuli.append(protocolProperties)
            
            #reset the stimulus window
            self.win.color = self.backgroundColor
            self.win.flip()
            
            #check if user wants to quit
        
        #clean up
        self.win.close()
        
        if self.useInformationMonitor:
            e.informationWin.close()
        
        core.quit()
        
class protocol():
    def __init__(self):
        self.preTime = 1 #s
        self.stimTime = 1 #s
        self.tailTime = 1 #s
        
        self.stimulusStartLog = []
        self.stimulusEndLog = []
        self.pauseTimeLog = []
        self.RandomSeed = random.random()
        random.seed(self.RandomSeed)
        
        self.completed = -1 # -1 indicates stimulus never ran. 0 indicates stimulus started but ended early. 1 indicates stimulus ran to completion

    def getFR(self, win):
        self.FR = win.getActualFrameRate()

        self.preTimeNumFrames = round(self.FR*self.preTime)
        self.stimTimeNumFrames = round(self.FR*self.stimTime)
        self.tailTimeNumFrames = round(self.FR*self.tailTime)

        self.actualPreTime = self.preTimeNumFrames * self.FR
        self.actualStimTime = self.stimTimeNumFrames * self.FR
        self.actualTailTime = self.tailTimeNumFrames * self.FR
        
    def getPixPerDeg(self, stimMonitor): 
        mon = monitors.Monitor(stimMonitor.name)
        eyeDistance = mon.getDistance()
        numPixelsWide = mon.currentCalib['sizePix'][0]
        cmWide = mon.currentCalib['width']
        totalVisualDegrees = 2*math.degrees(math.atan((cmWide/2)/eyeDistance))
        return numPixelsWide/totalVisualDegrees
    
    def showInformationText(self, stimWin, txt):
        if self.informationWin[0]:
            win = self.informationWin[1]
        else:
            win = stimWin
        
        informationalText = visual.TextStim(
                                    win = win, 
                                    text = txt)

        informationalText.draw()
        win.flip()

            
        
class MovingBar(protocol):
    def __init__(self):
        super().__init__()
        self.protocolName = 'MovingBar'
        self.orientations = [x*45 for x in range(8)]
        self.barWidth = 3.23 #deg
        self.barHeight = 100 #deg
        self.speed = 10 #deg/s
        self.barColor = [1, 1, 1]
        self.backgroundColor = [-1, -1, -1]
        self.stimulusReps = 3
        self.preTime = 1 #s
        self.stimTime = 7 #s
        self.tailTime = 1 #s
        
    def createOrientationLog(self):
        orientations = self.orientations
        self.orientationLog = []
        for n in range(self.stimulusReps):
            self.orientationLog += random.sample(orientations, len(orientations))
            
    def run(self, win, informationWin):
        self.completed = 0
        
        self.informationWin = informationWin #save here so you don't have to pass this as a function parameter every time you use it
        
        stimMonitor = win.monitor
        pixPerDeg = self.getPixPerDeg(stimMonitor)
        self.getFR(win)
        
        barHeightPix = pixPerDeg *self.barHeight
        barWidthPix = pixPerDeg * self.barWidth
        
        self.showInformationText(win, 'Stimulus Information: Moving Bar\nPress any key to begin')
        event.waitKeys() #wait for key press

        winWidth = win.size[0]
        winHeight = win.size[1]
        winCenter = [0, 0]
        winRadius = ((winWidth/2)**2 + (winHeight/2)**2)**0.5
        pixPerFrame = self.speed * pixPerDeg * (1/self.FR) #in units: deg/s * pix/deg * s/frame = pixPerFrame 
        trialClock = core.Clock() #this will reset every trial
        self.createOrientationLog()
        
        
        bar = visual.Rect(
                win,
                width = barWidthPix,
                height = barHeightPix,
                fillColor = self.barColor,
                )
        
        totalEpochs = len(self.orientationLog)
        epochNum = 0
        for ori in self.orientationLog:
            epochNum += 1
            #set initial bar position
            radiansOri = math.radians(ori)
            initialPosition = [-math.cos(radiansOri)*winRadius+winCenter[0], -math.sin(radiansOri)*winRadius+winCenter[1]]
            speedComponents = [math.cos(radiansOri)*pixPerFrame, math.sin(radiansOri)*pixPerFrame];
            
            #move bar by the proper components given the stimulus
            bar.opacity = 0
            bar.pos = initialPosition
            bar.ori = -ori
            self.stimulusStartLog.append(trialClock.getTime())
            if self.informationWin[0]:
                self.showInformationText(win, 'Running Moving Bar. Current orientation = ' + \
                                         str(ori) + '\n Epoch ' + str(epochNum) + ' of ' + str(totalEpochs))
            
            for f in range(self.preTimeNumFrames):
                win.flip()
                allKeys = event.getKeys() #check if user wants to quit early
                if len(allKeys)>0:
                    if 'q' in allKeys:
                        return
            
            bar.opacity = 1
            for f in range(self.stimTimeNumFrames):
                bar.pos += speedComponents
                bar.draw()
                win.flip()
                allKeys = event.getKeys() #check if user wants to quit early
                if len(allKeys)>0:
                    if 'q' in allKeys:
                        return
                    
            #remove bar at the end of the stimulus and wait the post time
            bar.opacity = 0
            for f in range(self.tailTimeNumFrames):
                win.flip()
                allKeys = event.getKeys() #check if user wants to quit early
                if len(allKeys)>0:
                    if 'q' in allKeys:
                        return
        
            
            self.stimulusEndLog.append(trialClock.getTime())
        
                
            
        
        self.StimulusDurations = numpy.subtract(self.stimulusEndLog, self.stimulusStartLog)
        self.completed = 1
        
def MovingGrating(protocol):
    def __init__(self):
        super().__init__()
        
        
        
#test experiment
e = experiment()

b = MovingBar()

b.stimTime = 3

b.orientations = [11, -50]

b. stimulusReps = 2

b2 = MovingBar()

b2.stimTime = 5

e.addProtocol(b)

e.addProtocol(b2)

e.activate()