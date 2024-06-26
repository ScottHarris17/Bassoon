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
from datetime import datetime

class experiment():
    def __init__(self):
        self.protocolList = []

        self.experimentDate = datetime.now().strftime("%D %H:%M:%S")
        self.activated = False

        self.allowGUI = True
        self.screen = 0
        self.fullscr = False
        self.backgroundColor = [-1, -1, -1] #doesn't do much, more or less obsolete because it's hardly seen
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
        self.ttlPortOpen = False #tracks whether the TTL port is open or not (not whether it's ON or OFF, but if the port itself is open and ready for commands)

        self.warpFileName = 'Warp File Location' #must be .data
        self.useFBO = False

        self.FR = 0 #frame rate of the stimulus window
        
        self.recompileExperiment = False  # option that is used by self.saveExperiment()

        self.timingReport = False
        
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
                    portInfo = configOptions['experiment']['ttlPort']
                    if self.writeTTL != "None":
                        self.establishPort(portInfo)
                    
                    self.useFBO = configOptions['experiment']['useFBO']
                    self.warpFileName = configOptions['experiment']['warpFileName']
                    
                    #add new options here so that they don't mess up old file formats
                    self.ttlBookmarks = configOptions['experiment']['ttlBookmarks']
                    self.timingReport = configOptions['experiment']['timingReport']
                    self.recompileExperiment = configOptions['experiment']['recompileExperiment']
                except:
                    print('*** Could not load all configuration settings from src/configOptions.json. Manually apply settings in the Options menu.')


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


    def establishPort(self, portInfo, fromSave = False):
        '''
        This function is used to open the COM/USB/serial/TTL port that is used for timing signals. It is critical that this port persists/remains open so long as the app is running/a port has been set. If the experiment object is deleted, the port attribute is deleted, or the port itself is closed, the voltage will revert back to its default state, making it difficult to control. This messes up timing protocols, so instead, keep the same port open for the duration of the experiment(s). Note: this scheme of keeping the port continuously open is an update as of 6/7/2024

        The port is purposefully closed when an experiment is saved, however, because it cannot be serialized (I think). This function is then called again after saving to re-establish the port.
        
        Inputs:
            - portInfo = the information about the selected port that is returned by serial.tools.list_ports.comports()
            - fromSave = boolean value that indicates whether this function is being called from the saveExperiment() function in main.py
        '''
        
        if self.ttlPortOpen: #check if there is an open port. If so, close it so that you can reconnect or connect to a different port
            print('--> Closing old TTL port')
            self.ttlPortOpen = False
            self.portObj.close() #close the open port if one is open that has a DIFFERENT name than the new one
        
        if self.writeTTL != ('Sustained' or 'Pulse'):
            return #just in case, make sure this function is only called when the writeTTL option is set to Sustained
        
        if portInfo == 'No Available Ports' or portInfo == '':
            return #check to make sure a real port has been selected
        
        #get port name
        if fromSave:
            portName = portInfo
        else:   
            portName = portInfo[:portInfo.find(' ')] #PARSING FOR HOW PORT NAME IS DETERMINED - may need to be manually adjusted based on operating system
            
        self.ttlPort = portName
        
        #if self.ttlPort is blank, then self.writeTTL must be None
        if self.ttlPort.strip() == '':
            self.writeTTL = 'None'
            return
        
        try:
            if self.writeTTL == 'Sustained':
                self.portObj = serial.Serial(portName)
                self.portObj.rts = True #set the RTS value to True, moving the voltage to 0
            elif self.writeTTL == 'Pulse':
                self.portObj = serial.Serial(portName, 4000000)   
            self.ttlPortOpen = True
            print('--> New TTL port has been opened')
        except serial.serialutil.SerialException:
            print('***IMPORTANT: It looks like the port you are trying to access is already in use. It may be open in a different program, or it may have never been closed by a previous instance of Bassoon. It is recommended that you close python and restart Bassoon to release the port')
            self.writeTTL = 'None'
            self.ttlPort = ''
        except:
            print('***Could not open or set the serial port called ', portName, '. Ensure you\'ve selected the proper port and try again. (If this error persists, see the experiment.establishPort() method. You may need to change the parsing for how the port name is determined depending on your operating system).')
            self.writeTTL = 'None'
            self.ttlPort = ''
        
        #The port should now stay open for as long as the experiment persists. If a new experiment is loaded in, the port should be reset and reopened. If the experiment is saved, the port will be temporarily closed, deleted, and then reestablished and opened
        return
        
        
        
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
                    allowStencil = self.allowStencil
                    )

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
            name = p[0] #note: p is not a deep copy, so the pointer in memory is to the same location as the protocol in self.protocolList and app.experiment.protocolList
            suffix = p[1].suffix
            
            if suffix == '_' or suffix.strip() == '':
                displayName = name
            else:
                displayName = name + suffix

            print('!!! Running Protocol Number ' + str(i+1) + ' of ' +  str(len(self.protocolList)) + ', with name ' + displayName)
            p = p[1] #the protocol object is the second one in the tuple

            #assign relevant experiment properties to the protocol
            p._timingReport = self.timingReport
            if hasattr(p, '_angleOffset'):
                p._angleOffset = self.angleOffset

            p.writeTTL = self.writeTTL #set the TTL write mode (inherits from the experiment)

            #set up the TTL ports based on the mode.
            if self.writeTTL == 'Pulse':
                if not hasattr(self, 'portObj'):
                    print('\n***NOTICE: stimulus ', i, 'was skipped because a TTL write method was selected, but no port has been connected to.')
                    continue
                p._portObj = self.portObj #initialize portObj for sending TTL pulses
                p._portObj.rts = True #ensure TTL is OFF to begin
                p.burstTTL(self.win) #execute a stereotyped burst to mark the start of the stimulus in pulse mode
            elif self.writeTTL == 'Sustained':
                if not hasattr(self, 'portObj'):
                    print('\n***NOTICE: stimulus ', i, 'was skipped because a TTL write method was selected, but no port has been connected to.')
                    continue
                p._portObj = self.portObj
                p._portObj.rts = True #ensure TTL is OFF to begin
                p._TTLON = False #used to track state of sustained TTL pulses                
               
                if self.ttlBookmarks: #Run the bookmark before the start of each stimulus: this is 1 frame on, 2 frames off, 3 frames on, 4 frames Off, 5 frames On, 6 frames Off at the frame frate of self.win The port should end in the off position again. Range is not inclusive
                    self.win.flip() #brief pause at frame rate in case there was just another flip from the previous stimulus (e.g., on the last frame of the previous stimulus)
                    for i in range(1, 7):
                        p.sendTTL(bookmark = True)
                        for m in range(i): #flip a number of frames that is equal to the iteration number
                            self.win.flip()
                    
                    #just ensure that the TTL pulse is actually off:
                    if p._TTLON:            
                        p.sendTTL(bookmark = True)
                    

            #run the protocol
            p.run(self.win, (self.useInformationMonitor, self.informationWin)) #send informationMonitor information as a tuple: bool (whether to use), window object
            
            #Make sure TTL port is turned OFF if running in sustained mode (it's often left on if the user quits a stimulus early)
            if self.writeTTL == 'Sustained' and p._TTLON:
                p.sendTTL()
                                
            #print the timing report if the user asks for it
            if p._timingReport:
                p.reportTime(displayName)
               

            #write down properties from previous stimulus
            protocolProperties = vars(p)
            protocolProperties.pop('_informationWin', None) #can't save ongoing psychopy win so remove it
            self.loggedStimuli.append(protocolProperties)



        #clean up after the activation loop
        self.win.close()

        if self.useInformationMonitor:
            self.informationWin.close()
            