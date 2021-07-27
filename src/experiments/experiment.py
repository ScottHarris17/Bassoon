# -*- coding: utf-8 -*-
"""
Created on Fri Jul  9 17:24:12 2021

@author: mrsco
"""
from psychopy import core, visual, data, event, monitors
import serial
import json
from pathlib import Path

class experiment():
    def __init__(self):
        self.protocolList = []

        self.experimentDate = 0
        self.activated = False

        self.allowGUI = True
        self.screen = 0
        self.fullscr = False
        self.backgroundColor = [-1, -1, -1]
        self.units = 'pix'
        self.allowStencil = True
        self.stimMonitor = 'testMonitor'

        self.useInformationMonitor = False
        self.informationMonitor = 'testMonitor'
        self.informationWin = None #will become a process. Must destroy to pickle the experiment object
        self.informationScreen = 0
        self.informationFullScreen = False

        self.estimatedTotalTime = 0

        self.loggedStimuli = []

        self.userInitiated = False #If True, the user will have to manually start each stimulus. Can also set this property manually for each stimulus

        self.writeTTL = 'None' #can be 'None', 'Pulse', 'Sustained'
        self.ttlPort = ''

        self.warpFileName = 'Warp File Location' #must be .data
        self.useFBO = False

        #Load previously saved experimental settings from configOptions.json
        if Path('configOptions.json').is_file():
            with open('configOptions.json') as f:
                configOptions = json.load(f)
                #stimWindow
                self.screen = configOptions['stimWindow']['screen']
                self.fullscr = configOptions['stimWindow']['fullscr']
                self.stimMonitor = configOptions['stimWindow']['stimMonitor']
                #infoWindow
                self.useInformationMonitor = configOptions['infoWindow']['useInformationMonitor']
                self.informationMonitor = configOptions['infoWindow']['informationMonitor']
                self.informationFullScreen = configOptions['infoWindow']['informationFullScreen']
                self.informationScreen = configOptions['infoWindow']['informationScreen']
                #experiment
                self.userInitiated = configOptions['experiment']['userInitiated']
                self.writeTTL = configOptions['experiment']['writeTTL']
                self.ttlPort = configOptions['experiment']['ttlPort']
                self.useFBO = configOptions['experiment']['useFBO']
                self.warpFileName = configOptions['experiment']['warpFileName']


    def addProtocol(self, newProtocol):
        '''
        Add a protocol to the experiment
        '''
        self.protocolList.append((newProtocol.protocolName, newProtocol))

        estimatedTotalTime = 0
        for tup in self.protocolList:
            estimatedTime_protocol = tup[1].estimateTime() #each protocol object should have a method called self.estimateTime
            estimatedTotalTime += estimatedTime_protocol

        self.estimatedTotalTime = estimatedTotalTime #store total estimated time in self.estimatedTotalTime


    def activate(self):
        '''
        Begin the experiment
        '''

        self.win = visual.Window(
                    allowGUI=self.allowGUI,
                    monitor = self.stimMonitor,
                    screen = self.screen,
                    fullscr = self.fullscr,
                    color = self.backgroundColor,
                    units = self.units,
                    useFBO = self.useFBO,
                    allowStencil = self.allowStencil)

        if self.useFBO:
            warper = visual.windowwarp.Warper(
                self.win,
                warpfile = self.warpFileName
                )

        #if the user would like to uise a second screen to display stimulus information then initialize that screen here
        #the flips to this second window must be called in the stimulus protocol itself
        if self.useInformationMonitor:
            self.informationWin = visual.Window(
                        allowGUI = self.allowGUI,
                        monitor = self.informationMonitor,
                        screen = self.informationScreen,
                        color = self.backgroundColor,
                        fullscr = self.informationFullScreen,
                        units = self.units,
                        )


        self.activated = True
        self.loggedStimuli = [] #always resets on a new run
        for i, p in enumerate(self.protocolList):
            print('!!! Running Protocol Number ' + str(i+1) + ' of ' +  str(len(self.protocolList)))
            p = p[1] #the protocol object is the second one in the tuple
            p.writeTTL = self.writeTTL
            
            if self.writeTTL == 'Pulse':
                portNameSerial = self.ttlPort[:self.ttlPort.find(' ')] #serial.Serial will only use beginning of port name
                p._portObj = serial.Serial(portNameSerial, 1000000) #initialize port_Obj for sending TTL pulses
            elif self.writeTTL == 'Sustained':
                portNameSerial = self.ttlPort[:self.ttlPort.find(' ')]
                p._portObj = serial.Serial(portNameSerial)
                p._TTLON = False #used to track state of sustained TTL pulses
                
            p.run(self.win, (self.useInformationMonitor, self.informationWin)) #send informationMonitor information as a tuple: bool (whether to use), window object

            #write down properties from previous stimulus
            protocolProperties = vars(p)
            protocolProperties.pop('_informationWin', None) #can't save ongoing psychopy win so remove it
            self.loggedStimuli.append(protocolProperties)

            #reset the stimulus window
            self.win.color = self.backgroundColor
            self.win.flip()

            #check if user wants to quit

        #clean up
        self.win.close()

        if self.useInformationMonitor:
            self.informationWin.close()
