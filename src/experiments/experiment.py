# -*- coding: utf-8 -*-
"""
Created on Fri Jul  9 17:24:12 2021

@author: mrsco
"""
from psychopy import core, visual, data, event, monitors
from psychopy.visual.windowwarp import Warper
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
        self.backgroundColor = [-1, -1, -1] #doesn't do much, more or less obselete because it's hardly seen
        self.units = 'pix'
        self.allowStencil = True
        self.stimMonitor = 'testMonitor'
        self.gamma = 2.0 #Default gamma value, will be updated from calibration.

        self.useInformationMonitor = False
        self.informationMonitor = 'testMonitor'
        self.informationWin = None #will become a process. Must destroy to pickle the experiment object
        self.informationScreen = 0
        self.informationFullScreen = False

        self.estimatedTotalTime = 0

        self.loggedStimuli = []

        self.userInitiated = False #If True, the user will have to manually start each stimulus. Can also set this property manually for each stimulus
        self.angleOffset = 0.0 #deg - offset for directional stimuli

        self.writeTTL = 'None' #can be 'None', 'Pulse', 'Sustained'
        self.ttlBookmarks = False #used for sustained mode only to send stereotyped bookmark patterns before each stimulus
        self.ttlPort = ''
        

        self.warpFileName = 'Warp File Location' #must be .data
        self.useFBO = False

        self.FR = 0 #frame rate of the stimulus window
                
        #Load previously saved experimental settings from configOptions.json
        if Path('configOptions.json').is_file():
            with open('configOptions.json') as f:
                try:
                    configOptions = json.load(f)
                    #stimWindow
                    self.screen = configOptions['stimWindow']['screen']
                    self.fullscr = configOptions['stimWindow']['fullscr']
                    self.stimMonitor = configOptions['stimWindow']['stimMonitor']
                    try:
                        self.gamma = configOptions['stimWindow']['gamma']
                    except Exception as e:
                        print('*** Could not load gamma from config. Please calibrate to set new gamma.')
                    #infoWindow
                    self.useInformationMonitor = configOptions['infoWindow']['useInformationMonitor']
                    self.informationMonitor = configOptions['infoWindow']['informationMonitor']
                    self.informationFullScreen = configOptions['infoWindow']['informationFullScreen']
                    self.informationScreen = configOptions['infoWindow']['informationScreen']
                    #experiment
                    self.userInitiated = configOptions['experiment']['userInitiated']
                    self.angleOffset = float(configOptions['experiment']['angleOffset'])
                    self.writeTTL = configOptions['experiment']['writeTTL']
                    if isinstance(self.writeTTL, bool):
                        self.writeTTL = "None"
                    self.ttlPort = configOptions['experiment']['ttlPort']
                    self.useFBO = configOptions['experiment']['useFBO']
                    self.warpFileName = configOptions['experiment']['warpFileName']
                    
                    #add new options here so that they don't mess up old file formats
                    self.ttlBookmarks = configOptions['experiment']['ttlBookmarks']
                except:
                    print('*** Could not load all configuration settings from src/configOptions.json. Manually apply settings in the Options menu')


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
                    allowGUI = self.allowGUI,
                    monitor = self.stimMonitor,
                    screen = self.screen,
                    fullscr = self.fullscr,
                    color = self.backgroundColor,
                    units = self.units,
                    useFBO = self.useFBO,
                    allowStencil = self.allowStencil)

        self.FR = self.win.getActualFrameRate() #log the frame rate of the stimulus window

        #set a warper if you want to morph the stimulus
        if self.useFBO:
            warper = Warper(
                self.win,
                warp = 'warpfile',
                warpfile = self.warpFileName
                )

        #if the user would like to use a second screen to display stimulus information then initialize that screen here
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

            #assign relevant experiment properties to the protocol
            if hasattr(p, '_angleOffset'):
                p._angleOffset = self.angleOffset

            p.writeTTL = self.writeTTL #set the TTL write mode (inherits from the experiment)

            #set up the TTL ports based on the mode.
            if self.writeTTL == 'Pulse':
                portNameSerial = self.ttlPort[:self.ttlPort.find(' ')] #serial.Serial will only use beginning of port name
                p._portObj = serial.Serial(portNameSerial, 4000000) #initialize port_Obj for sending TTL pulses
                p._portObj.setRTS(True) #ensure TTL is OFF to begin
                p.burstTTL(self.win) #execute a stereotyped burst to mark the start of the stimulus in pulse mode
            elif self.writeTTL == 'Sustained':
                portNameSerial = self.ttlPort[:self.ttlPort.find(' ')]
                p._portObj = serial.Serial(portNameSerial)
                p._portObj.setRTS(True) #ensure TTL is OFF to begin
                p._TTLON = False #used to track state of sustained TTL pulses                
               
                if self.ttlBookmarks: #Run the bookmark. before the start of each stimulus: this is 1 frame on, 2 frames off, 3 frames on, 4 frames Off, 5 frames On, 6 frames Off at the frame frate of self.win The port should end in the off position again. Range is not inclusive
                    for i in range(1, 7):
                        if p._TTLON: #if TTL is on, turn it off
                            p._portObj.setRTS(True)
                            p._TTLON = False
                        else: #if TTL is off, turn it on
                            p._portObj.setRTS(False)
                            p._TTLON = True
                        for m in range(i): #flip a number of frames that is equal to the iteration number
                            self.win.flip()
                    
                    #just ensure that the TTL pulse is actually off:
                    p._portObj.setRTS(True) #ensure TTL is OFF to begin
                    p._TTLON = False #used to track state of sustained TTL pulses                
                    
                                

            #run the protocol
            p.run(self.win, (self.useInformationMonitor, self.informationWin)) #send informationMonitor information as a tuple: bool (whether to use), window object
            
            #Make sure TTL port is turned OFF if running in sustained mode (it's often left on if the user quits a stimulus early)
            if self.writeTTL == 'Sustained':
                p._portObj.setRTS(True)
                p._TTLON = False

            #write down properties from previous stimulus
            protocolProperties = vars(p)
            protocolProperties.pop('_informationWin', None) #can't save ongoing psychopy win so remove it
            self.loggedStimuli.append(protocolProperties)



        #clean up after the activation loop
        self.win.close()

        if self.useInformationMonitor:
            self.informationWin.close()
            