# -*- coding: utf-8 -*-
"""
Created on Fri Jul  9 17:23:23 2021

Welcome to Bassoon. Run this file to open the GUI.

You must have psychopy libraries installed to use built in stimuli and to achieve the necessary imports.
www.psychopy.org

Experiments can be managed through the GUI or programmatically. See README.md for help.

@author: Scott Harris
scott.harris@ucsf.edu

Copyright 2021 under MIT open source license.
"""
import os
from tkinter import *
import tkinter.ttk as ttk
import tkinter.filedialog as tkfd
from psychopy import core, visual, data, event, monitors
from psychopy.tools.filetools import fromFile, toFile
import serial
import serial.tools.list_ports as list_ports
from datetime import datetime
import pickle
import json
import math
import time
import copy
import random

# Each protocol subclass must be imported here:
from experiments.experiment import experiment
from protocols.protocol import protocol
from protocols.Flash import Flash
from protocols.Pause import Pause
from protocols.MovingBar import MovingBar
from protocols.FlashFamily import FlashFamily
from protocols.CheckerboardReceptiveField import CheckerboardReceptiveField
from protocols.MovingGratingDirection import MovingGratingDirection
from protocols.OscillatingGrating import OscillatingGrating
from protocols.PupilCalibration import PupilCalibration
from protocols.StaticGrating import StaticGrating
from protocols.SnellenShapes import SnellenShapes
from protocols.DriftingNoise import DriftingNoise
from protocols.FlashGrid import FlashGrid
from protocols.ImageJitter import ImageJitter
from protocols.ScotomaMovingGrating import ScotomaMovingGrating

class Bassoon:
    def __init__(self, master):
        master.title('Bassoon App')
        # initialize the experiment
        self.experiment = experiment()

        # create mainframe and menu
        self.frame = Frame(master)
        self.frame.pack(fill="both", expand=True)
        self.menubar = Menu(root)
        self.menubar.add_command(label="Load Experiment", command=self.loadExperiment)
        self.optionsMenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_command(label="Options", command=self.editExperiment)
        self.menubar.add_command(label ="Quick Actions", command=self.quickActionsWin)
        self.menubar.add_command(label="Quit", command=self.frame.quit)
        master.config(menu=self.menubar)

        # Create a label that will provide the name of the database that is open
        self.namelabel_text = StringVar()
        self.namelabel = Label(self.frame, textvariable=self.namelabel_text)
        self.namelabel_text.set("Bassoon")
        self.namelabel.config(font=("Helvetica", 30))
        self.namelabel.pack(side='top')

        # assemble the protocol list to be used in the dropdown menu
        self.listProtocols()

        # protocol dropdown menu
        self.protocolSelection = StringVar(root)
        self.protocolSelection.set(self.protocolList[0])
        self.protocolLabel = Label(self.frame, text='Available Stimuli', font=("Helvetica", 15))
        self.protocolLabel.pack()
        self.protocolDropdown = OptionMenu(self.frame, self.protocolSelection, *self.protocolList)
        self.protocolDropdown.pack()

        # index label
        self.indexLabel = Label(self.frame, text='Protocol Index (int):').pack()
        self.protocolIndexField = Entry(self.frame)
        self.protocolIndexField.insert(END, '1')  # initial value
        self.protocolIndexField.pack()

        # add button
        self.addProtocolButton = Button(
            self.frame, text='Add Stimulus', command=lambda: self.addProtocol())
        self.addProtocolButton.pack()

        self.scrollbarY = Scrollbar(self.frame, orient=VERTICAL)
        self.scrollbarY.pack(side=RIGHT, fill=Y)

        # list box
        self.experimentSketchBox = Listbox(self.frame)
        self.experimentSketchBox.pack(fill="both", expand=True)
        self.experimentSketchBox.config(yscrollcommand=self.scrollbarY.set)
        self.scrollbarY.config(command=self.experimentSketchBox.yview)

        self.estimatedTimeLabel = Label(
            self.frame, text='Estimated Time: 0m 0s')
        self.estimatedTimeLabel.pack()

        # list of tuples. Position 1 = protocol name. Position 2 = protocol object
        self.experimentSketch = []

        # save options
        self.recompileExperiment = True  # option that is used by self.saveExperiment()

        # button grid at bottom
        self.buttonFrame = Frame(self.frame)
        self.editProtocolButton = Button(
            self.buttonFrame, text='Edit', command=lambda: self.editProtocol())
        self.editProtocolButton.grid(row=1, column=1)
        self.removeProtocolButton = Button(
            self.buttonFrame, text='Remove', command=lambda: self.removeProtocol())
        self.removeProtocolButton.grid(row=1, column=2)
        self.saveExperimentButton = Button(
            self.buttonFrame, text='Save', command=lambda: self.saveExperiment())
        self.saveExperimentButton.grid(row=1, column=3)
        self.runExperimentButton = Button(
            self.buttonFrame, text='Run Experiment', command=lambda: self.runExperiment())
        self.runExperimentButton.grid(row=1, column=4)
        self.buttonFrame.pack()

        #load rig configuration
        #self.loadRigPreferences()


        print("\n\n\n-------------------Bassoon App-------------------")
        print("--> Initialization Complete!")
        print("--> Bassoon is playing!")

        # print the welcomeArt in the console
        print('\n')
        with open('images/welcomeArt.txt', 'r') as f:
            [print(line[1:-1]) for line in f]

        print("\n\n--> Use the GUI to Generate New Psychopy Experiments\n")


    def loadExperiment(self):
        '''
        Load an experiment that was previously built. This can either be a new experiment that has never been run, or an experiment that has been run before. In either case, a new experiment will be loaded into Bassoon. Properties of each protocol will be set according to those in the loaded experiment when possible. However, only attributes that are set before a protocol is run will be loaded. Properties that are set during the running of an experiment and private properties that start with '_' will not be updated.
        '''
        with tkfd.askopenfile(mode='rb', title="Select a file", filetypes=(("Experiment Files", "*.experiment"), ("python files", "*.py"), ("all files", "*.*"))) as exp:
            newExperimentTemplate = pickle.load(exp)

        self.experimentSketch = []  # clear experiment sketch if it was filled before this

        newExperiment = experiment() #load a new experiment object to fill
        # iterate through the stored protocols and add them and their names to
        # the experiment sketch. Then, update
        for num, p in enumerate(newExperimentTemplate.protocolList):
            if type(p) != tuple:
                print('***Error loading protocol', p, 'Not of type tuple')

            pname = p[0] #.json files will have
            newObj = eval(pname+'()') #get a new object of the correct name
            newAttributes = list(vars(newObj).keys()) #list the attributes for this new obj
            for a in newAttributes: #cycle through the attributes
                if not a.startswith('_'): #get values from the loaded experiment for attributes that don't start with '_'
                    try:
                        assignment = getattr(p[1], a)
                        setattr(newObj, a, assignment)
                    except: #catch if the logged stimulus doesn't have the 'a' attribute or 'num' protocol
                        print('***Could not set properties for attribute ' + str(a) +' in protocol number ' + str(num) + ' with name ' + pname + ' because the loaded experiment was missing this attribute')


            #build the display name
            pnameWithSpaces = ''
            for j, char in enumerate(pname):
                if char.isupper() and j != 0:
                    pnameWithSpaces += ' ' + char.lower()
                else:
                    pnameWithSpaces += char
            self.experimentSketch.append((pnameWithSpaces, newObj))

        self.updateExperimentSketch()

    #Used by options Warp File to find file path

    def listProtocols(self):
        '''
        Generate a list of available protocols to display in the dropdown menu
        '''
        protocolFiles = os.listdir('protocols')

        # save all available protocols
        self.protocolList = [p[:-3] for p in protocolFiles if p.endswith(
            '.py') and p != 'protocol.py' and p != '__init__.py']
        self.protocolList.sort()
        for i, pname in enumerate(self.protocolList):
            pnameWithSpaces = ''
            for j, char in enumerate(pname):
                if char.isupper() and j != 0:
                    pnameWithSpaces += ' ' + char.lower()
                else:
                    pnameWithSpaces += char

            self.protocolList[i] = pnameWithSpaces


    def changeProtocolIndex(self, e=0):
        '''
        Updates the protocolIndex field when the user makes a single right click
        e is a placeholder

        User must select with the left button and then hit the right button to
        call this function without error
        '''
        self.protocolIndexField.delete(0, END)
        try:
            selectionIndex = self.experimentSketchBox.curselection()[0]
        except:
            selectionIndex = 0
            print('\n???Select a protocol with the left mouse button first. Then Hit the right button to update the index field.')

        # python is 0 indexed but Bassoon GUI isn't so add 1
        self.protocolIndexField.insert(END, str(selectionIndex+1))


    def addProtocol(self):
        '''
        Adds a protocol to self.experimentSketch using the protocol ID selected
        from the self.protocolSelection dropdown menu and the index specified
        in the self.protocolIndexField edit field
        '''

        # first grab the desired index and check that it's valid
        index_input = self.protocolIndexField.get()
        try:
            index_int = int(index_input)
        except:
            print('***Invalid Entry: Insert an integer value in the input box that specifies where you would like to insert the stimulus.')
            return

        # check edge cases where index is too small and round it to the proper value
        if index_int <= 0:
            index_int = 1

        # convert the protocol name that you will add back to the module name that stores the protocol code
        pnameWithSpaces = self.protocolSelection.get()
        moduleName = ''
        nextCap = False
        for char in pnameWithSpaces:
            if char == ' ':
                nextCap = True
                continue
            else:
                if nextCap:
                    moduleName += char.upper()
                    nextCap = False
                else:
                    moduleName += char

        # insert a tuple into self.experimentSketch. The first index holds the name of the protocol as will be displayed in the list box. The second index holds the actual stimulus object that will be run during the experiment.
        protocolObject = eval(moduleName + '()')
        protocolObject.userInitiated = self.experiment.userInitiated
        if (len(self.experimentSketch) == 1 and index_int > 1)\
                or (index_int >= len(self.experimentSketch) and len(self.experimentSketch) != 1):
            self.experimentSketch.append((pnameWithSpaces, protocolObject))
        else:
            self.experimentSketch.insert(
                index_int-1, (pnameWithSpaces, protocolObject))

        # update the list box to reflect the new stimulus
        self.updateExperimentSketch()


    def quickActionsWin(self):
        '''
        Buttons for quickly executing commands on the spot
        '''
        
        #Quick action functions
        def FlipTTL(self, direction):
            '''Code change the TTL pulse if it exists'''
            if self.experiment.ttlPort == 'No Available Ports':
                print('Could not flip TTL because no port has been selected for this experiment')
                return
            else:
                portName = self.experiment.ttlPort
                portNameSerial = portName[:portName.find(' ')]
                portObj = serial.Serial(portNameSerial)
                if direction == 'Off':
                    portObj.setRTS(True) #turns OFF ttl
                    print('TTL set to OFF')
                elif direction == 'On':
                    portObj.setRTS(False) #turns OFF ttl
                    print('TTL set to ON')
            return
        
        
        def moveProtocol(self, currentIndx, newIndx):
            ''' Move a protocol at current index to newIndx in the experiment sketch'''
            try:
                currentIndx_int = int(currentIndx)
                newIndx_int = int(newIndx)
            except:
                print("***Could not move the stimulus. Check that index entries are integers")
                return
            
            if currentIndx_int > len(self.experimentSketch):
                print("***Could not move the stimulus. The value entered in the current index box is larger than the number of protocols that are currently in the experiment sketch.")
                return
            
            if currentIndx_int < 1 or newIndx_int < 1:
                print("***Could not move the stimulus. Enter index values of 1 or greater only.")
                return
            
            protocolTup = self.experimentSketch.pop(currentIndx_int - 1) #grabs the tuple of (protocol name, protocolObj) while simulatenously removing it from the list
                
            if (len(self.experimentSketch) == 1 and newIndx_int > 1)\
                    or (newIndx_int > len(self.experimentSketch) and len(self.experimentSketch) != 1):
                self.experimentSketch.append(protocolTup)
            else:
                self.experimentSketch.insert(
                    newIndx_int-1, protocolTup)
            
            # update the list box to reflect the new stimulus
            self.updateExperimentSketch()
            
            
        
        def copyAndPasteProtocol(self, currentIndx, newIndx):
            '''Copy a protocol at currentIndx to a slot at newIndx'''
            
            try:
                currentIndx_int = int(currentIndx)
                newIndx_int = int(newIndx)
            except:
                print("***Could not copy and paste the stimulus. Check that index entries are integers")
                return
            
            if currentIndx_int > len(self.experimentSketch):
                print("***Could not copy and paste the stimulus. The value entered in the current index box is larger than the number of protocols that are currently in the experiment sketch.")
                return
            
            if currentIndx_int < 1 or newIndx_int < 1:
                print("***Could not copy and paste the stimulus. Enter index values of 1 or greater only.")
                return
            
            protocolTup = copy.deepcopy(self.experimentSketch[currentIndx_int - 1]) #grabs the tuple of (protocol name, protocolObj)
            
            protocolTup[1].suffix += 'COPY' #update the suffix to indicate it's a copy

            if (len(self.experimentSketch) == 1 and newIndx_int > 1)\
                    or (newIndx_int >= len(self.experimentSketch) and len(self.experimentSketch) != 1):
                self.experimentSketch.append(protocolTup)
            else:
                self.experimentSketch.insert(
                    newIndx_int-1, protocolTup)
                
            # update the list box to reflect the new stimulus
            self.updateExperimentSketch()
            
            #open the edit menu for the new protocol to encourage the user to update it
            self.editProtocol(calledByCopy = (True, newIndx_int-1))
            
            
        def shuffleProtocolList(self):
            '''Shuffle the order of stimuli in the protocol list'''
            
            if len(self.experimentSketch) < 2:
                print('***Shuffling is not possible with less than 2 protocols in the protocol list')
                return
            
            random.shuffle(self.experimentSketch)
            
            # update the list box to reflect the new stimulus
            self.updateExperimentSketch()
            print('--> Shuffled!')            
        
        
        actionsWindow = Toplevel(root)
        actionsWindow.title('Quick Actions')
        
        actionFrame = Frame(actionsWindow, padx=20)
        actionFrame.pack(fill = "both", expand = True)
        
        actionLabel = Label(actionFrame, text = 'Quick Actions')
        actionLabel.config(font=("Helvetica, 14"))
        actionLabel.pack()
        
        comFrame = LabelFrame(actionFrame, text='Communications', bd=5, padx = 5, pady=10)
        comFrame.configure(font=("Helvetica", 12))
        comFrame.pack()
        
        #turn off the TTL channel
        flipTTLBtn = Button(comFrame, text = 'TTL Off', padx = 7, command = lambda: FlipTTL(self, 'Off'))
        flipTTLBtn.grid(row=2, column = 1)
        
        #turn on the TTL channel
        flipTTLBtn = Button(comFrame, text = 'TTL On', padx = 7, command = lambda: FlipTTL(self, 'On'))
        flipTTLBtn.grid(row=2, column = 3)
        
        
        #Move existing protocol
        moveFrame = LabelFrame(actionFrame, text='Move A Protocol', bd = 5, padx = 10, pady = 10)
        moveFrame.configure(font=("Helvetica", 12))
        moveFrame.pack()
        
        moveCurrentIndexLabel = Label(moveFrame, text = "Current Index", padx = 10)
        moveCurrentIndexLabel.grid(row = 0, column = 0) 
        moveCurrentIndexEntry = Entry(moveFrame)
        moveCurrentIndexEntry.grid(row = 1, column = 0)
        
        moveToIndexLabel = Label(moveFrame, text = "Move To Index", padx = 10)
        moveToIndexLabel.grid(row = 2, column = 0)
        moveToIndexEntry = Entry(moveFrame)
        moveToIndexEntry.grid(row = 3, column = 0)
        
        moveBtn = Button(moveFrame, text = 'Go', command = lambda: moveProtocol(self, moveCurrentIndexEntry.get(), moveToIndexEntry.get()))
        moveBtn.grid(row = 4, column = 0)
        
        moveNoteOnIndexingLabel = Label(moveFrame, text = "*Note that indexing starts with 1, not 0", font =("Helvetica 9 italic"), pady = 12)
        moveNoteOnIndexingLabel.grid(row = 5, column = 0)
        
        #copy existing protocol
        copyFrame = LabelFrame(actionFrame, text='Copy A Protocol', bd = 5, padx = 10, pady = 10)
        copyFrame.configure(font=("Helvetica", 12))
        copyFrame.pack()
        
        copyCurrentIndexLabel = Label(copyFrame, text = "Current Index", padx = 10)
        copyCurrentIndexLabel.grid(row = 0, column = 0) 
        copyCurrentIndexEntry = Entry(copyFrame)
        copyCurrentIndexEntry.grid(row = 1, column = 0)
        
        copyToIndexLabel = Label(copyFrame, text = "Copy To Index", padx = 10)
        copyToIndexLabel.grid(row = 2, column = 0)
        copyToIndexEntry = Entry(copyFrame)
        copyToIndexEntry.grid(row = 3, column = 0)
        
        copyBtn = Button(copyFrame, text = 'Go', command = lambda: copyAndPasteProtocol(self,  copyCurrentIndexEntry.get(), copyToIndexEntry.get()))
        copyBtn.grid(row = 4, column = 0)
        
        copyNoteOnIndexingLabel = Label(copyFrame, text = "*Note that indexing starts with 1, not 0", font =("Helvetica 9 italic"), pady = 12)
        copyNoteOnIndexingLabel.grid(row = 5, column = 0)
        
        #shuffle protocols
        shuffleFrame = LabelFrame(actionFrame, text='Shuffle Protocols', bd = 5, padx = 10, pady = 10)
        shuffleFrame.configure(font=("Helvetica", 12))
        shuffleFrame.pack()
        
        shuffleBtn = Button(shuffleFrame, text = 'Shuffle', command = lambda: shuffleProtocolList(self))
        shuffleBtn.pack(side=TOP)
        
        
 

    def editExperiment(self):
        '''
        Edit monitor options, save preferences, and more
        '''
        monitorEditWindow = Toplevel(root)
        monitorEditWindow.title('Edit Experiment')

        editFrame = Frame(monitorEditWindow, padx=20)
        editFrame.pack(fill="both", expand=True)

        # experiment options
        monitorLabel = Label(editFrame, text='Experiment Options')
        monitorLabel.config(font=("Helvetica", 14))
        monitorLabel.pack()

        # stimulus monitor selection
        stimulusFrame = LabelFrame(
            editFrame, text='Stimulus Monitor', bd=5, pady=10)
        stimulusFrame.configure(font=("Helvetica", 12))
        stimulusFrame.pack()

        monitorNames = monitors.getAllMonitors()

        # stimulus monitor name
        stimMonitorLabel = Label(stimulusFrame, text='Monitor', padx=10)
        stimMonitorLabel.grid(row=2, column=1)
        self.stimMonitorSelection = StringVar(root)
        self.stimMonitorSelection.set(self.experiment.stimMonitor)
        stimulusMonitorDropdown = OptionMenu(
            stimulusFrame, self.stimMonitorSelection, *monitorNames)
        stimulusMonitorDropdown.grid(row=2, column=2)

        # stimulus full screen
        stimulusFullScreenLabel = Label(
            stimulusFrame, text='Full Screen', padx=10)
        stimulusFullScreenLabel.grid(row=2, column=3)
        self.stimFullScreenSelection = IntVar(root)
        self.stimFullScreenSelection.set(self.experiment.fullscr == True)
        stimFullScreenChk = Checkbutton(
            stimulusFrame, var=self.stimFullScreenSelection)
        stimFullScreenChk.grid(row=2, column=4)

        # stimulus screen number
        stimScreenLabel = Label(stimulusFrame, text='Screen #', padx=10)
        stimScreenLabel.grid(row=2, column=5)
        self.stimScreenSelection = IntVar(root)
        self.stimScreenSelection.set(self.experiment.screen)
        stimScreenNumberDropdown = OptionMenu(
            stimulusFrame, self.stimScreenSelection, *[0, 1, 2, 3])
        stimScreenNumberDropdown.grid(row=2, column=6)

        # stimulus monitor gamma calibration
        self.calGamma = 2.0
        stimCalibrationLabel = Label(stimulusFrame, text='Calibrate gamma', padx=7)
        stimCalibrationLabel.grid(row=3, column=1)
        self.stimCalibrationBtn = Button(stimulusFrame, text='\u03B3 is {g}'.format(g=round(self.experiment.gamma,5)), padx=7, command= lambda: self.calibrateGammaMenu())
        self.stimCalibrationBtn.grid(row=3, column=2)

        # information monitor selection
        informationFrame = LabelFrame(
            editFrame, text='Information Monitor', bd=5, pady=10)
        informationFrame.configure(font=("Helvetica", 12))
        informationFrame.pack()

        # use information window
        informationUseLabel = Label(
            informationFrame, text='Use Information Window?')
        informationUseLabel.configure(font=('Helvetica', 12))
        informationUseLabel.grid(row=0, column=1, columnspan=3,  pady=(5, 10))
        self.informationUseSelection = IntVar(root)
        self.informationUseSelection.set(
            self.experiment.useInformationMonitor == True)
        informationUseChk = Checkbutton(
            informationFrame, var=self.informationUseSelection)
        informationUseChk.grid(row=0, column=4, pady=(5, 10))

        # informatin monitor name
        informationMonitorLabel = Label(
            informationFrame, text='Monitor', padx=10)
        informationMonitorLabel.grid(row=2, column=1)
        self.informationMonitorSelection = StringVar(root)
        self.informationMonitorSelection.set(
            self.experiment.informationMonitor)
        informationMonitorDropdown = OptionMenu(
            informationFrame, self.informationMonitorSelection, *monitorNames)
        informationMonitorDropdown.grid(row=2, column=2)

        # information full screen
        informationFullScreenLabel = Label(
            informationFrame, text='Full Screen', padx=10)
        informationFullScreenLabel.grid(row=2, column=3)
        self.informationFullScreenSelection = IntVar(root)
        self.informationFullScreenSelection.set(
            self.experiment.informationFullScreen == True)
        informationFullScreenChk = Checkbutton(
            informationFrame, var=self.informationFullScreenSelection)
        informationFullScreenChk.grid(row=2, column=4)

        # information screen number
        informationScreenLabel = Label(
            informationFrame, text='Screen #', padx=10)
        informationScreenLabel.grid(row=2, column=5)
        self.informationScreenSelection = IntVar(root)
        self.informationScreenSelection.set(self.experiment.informationScreen)
        informationScreenNumberDropdown = OptionMenu(
            informationFrame, self.informationScreenSelection, *[0, 1, 2, 3])
        informationScreenNumberDropdown.grid(row=2, column=6)

        # experiment options
        experimentFrame = LabelFrame(
            editFrame, text='Experiment', bd=6, pady=10)
        experimentFrame.configure(font=("Helvetica", 12))
        experimentFrame.pack()

        # user initiates protocols
        userInitLabel = Label(
            experimentFrame, text='Manually Initiate Each Protol', padx=10)
        userInitLabel.grid(row=0, column=0, columnspan=2)
        self.userInitSelection = IntVar(root)
        self.userInitSelection.set(self.experiment.userInitiated)
        userInitChk = Checkbutton(experimentFrame, var=self.userInitSelection)
        userInitChk.grid(row=0, column=2)

        #Angle offset value for directional stimuli
        angleOffsetLabel = Label(
            experimentFrame, text = 'Angle Offset', padx = 10)
        angleOffsetLabel.grid(row=0, column=3)
        self.angleOffsetSelection = StringVar(root)
        self.angleOffsetSelection.set(str(self.experiment.angleOffset))
        angleOffsetEntry = Entry(experimentFrame, textvariable = self.angleOffsetSelection, width = 6)
        angleOffsetEntry.grid(row=0, column=4)

        # write TTL pulses during stimulus
        writeTtlLabel = Label(
            experimentFrame, text='Write TTL Pulses', padx=10)
        writeTtlLabel.grid(row = 1, column = 0, columnspan = 2)
        self.writeTtlSelection = StringVar(root)
        self.writeTtlSelection.set(self.experiment.writeTTL)
        writeTtlDropdown = OptionMenu(experimentFrame, self.writeTtlSelection, *['None', 'Pulse', 'Sustained'])
        writeTtlDropdown.grid(row = 1, column = 2)
        
        #check box for TTL bookmarks between protocols in sustained mode
        ttlBookmarksLabel = Label(experimentFrame, text = 'TTL Bookmarks (for sustained mode only)', padx = 10)
        ttlBookmarksLabel.grid(row = 2, column = 0, columnspan = 2)
        self.ttlBookmarksSelection = IntVar(root)
        self.ttlBookmarksSelection.set(self.experiment.ttlBookmarks)
        ttlBookmarksChk = Checkbutton(experimentFrame, var=self.ttlBookmarksSelection)
        ttlBookmarksChk.grid(row = 2, column = 2, pady = 10)
        
           
        #choose ttl port
        ttlPortLabel = Label(experimentFrame, text = 'TTL Port', padx = 10)
        ttlPortLabel.grid(row = 1, column = 3)
        self.ttlPortSelection = StringVar(root)
        self.ttlPortSelection.set(self.experiment.ttlPort)
        availablePorts = list(list_ports.comports()) #get available com ports
        if len(availablePorts) == 0:
            availablePorts = ['No Available Ports']
        ttlPortDropDown = OptionMenu(experimentFrame, self.ttlPortSelection, *availablePorts)
        ttlPortDropDown.grid(row = 1, column = 4)

        #Framebuffer object selection (FBO)
        FBOLabel = Label(experimentFrame, text = 'Use FBO?', padx = 10) # Check to see if case exists where user passes morph file, but FBO is false
        FBOLabel.grid(row = 3, column = 0)
        self.FBObjectSelection = IntVar(root)
        self.FBObjectSelection.set(self.experiment.useFBO)
        writeFBOChk = Checkbutton(experimentFrame, var=self.FBObjectSelection)
        writeFBOChk.grid(row = 3, column = 1, pady = 10)

        #Warp file location
        #warpLabel = Label(experimentFrame, text = 'Warp File Location', padx = 10)
        #warpLabel.grid(row = 4, column = 0, columnspan=2)
        self.WarpSelection = StringVar(root)
        self.WarpSelection.set(self.experiment.warpFileName)
        warpFileEnt = Entry(experimentFrame, textvariable = self.WarpSelection, width = 30)
        warpFileEnt.grid(row = 3, column=2, columnspan = 2)
        warpFileSelectBtn = Button(experimentFrame, text = 'Browse', padx = 7, command = lambda: self.findWarpFiletoSave(monitorEditWindow,warpFileEnt))
        warpFileSelectBtn.grid(row = 3, column = 4)

        #Recompile during save
        recompileLabel = Label(
            experimentFrame, text='Recompile Experiment When Saving', padx=10)
        recompileLabel.grid(row=4, column=0, columnspan=3)
        self.recompileSelection = IntVar(root)
        self.recompileSelection.set(self.recompileExperiment)
        recompileChk = Checkbutton(
            experimentFrame, var=self.recompileSelection)
        recompileChk.grid(row=4, column=3)
        
        #timing report
        timingReportLabel = Label(
            experimentFrame, text='Print Timing Reports', padx=10)
        timingReportLabel.grid(row=5, column = 0, columnspan=3)
        self.timingReportSelection = IntVar(root)
        self.timingReportSelection.set(self.experiment.timingReport)
        timingReportChk = Checkbutton(
            experimentFrame, var=self.timingReportSelection)
        timingReportChk.grid(row=5, column=3)

        # add apply and close buttons
        buttonFrame = Frame(editFrame)
        buttonFrame.pack()
        applyButton = Button(buttonFrame, text='Apply Changes',
                             command=self.applyExperimentChanges)
        applyButton.grid(row=0, column=0, padx = 2)
        saveButton = Button(buttonFrame, text='Save & Apply Changes',
                             command=self.setConfigFile)
        saveButton.grid(row=0, column=1, padx = 2)
        closeButton = Button(buttonFrame, text='Close Window',
                             command=lambda: monitorEditWindow.destroy())
        closeButton.grid(row=0, column=2)

    # Gamma calibration of monitor
    def calibrateGammaMenu(self):
        '''Calibrate gamma value of stimulus monitor'''
        # create subwindow for calibration
        calibWindow = Toplevel(root)
        calibWindow.title('Calibration')
        calibWindow.geometry('550x250')

        calibFrame = Frame(calibWindow, padx=20)
        calibFrame.pack(fill="both", expand=True)

        # 'enter values for gamma calibration' section
        gammaFrame = LabelFrame(calibFrame, text='Gamma Calibration', bd=3, pady=10)
        gammaFrame.configure(font=("Helvetica", 14))
        gammaFrame.pack()

        stepsLabel = Label(gammaFrame,text='Luminance step size', padx=10)
        stepsLabel.grid(row=1,column=1)
        steps = DoubleVar(root)
        steps.set(0.1)
        stepsDropdown = OptionMenu(gammaFrame, steps, *[0.1 , 0.2, 0.4])
        stepsDropdown.grid(row=1,column=2)

        pixelEntLabel = Label(gammaFrame,text='Current Pixel Value',padx=10)
        pixelEntLabel.grid(row=2,column=1)
        pVal = DoubleVar()
        pixelEntry = Entry(gammaFrame,textvariable=pVal,bg='#FFFDD0')
        pixelEntry.grid(row=3,column=1)
        lumEntLabel = Label(gammaFrame,text='Measure Luminance',padx=10)
        lumEntLabel.grid(row=2,column=2)

        lVal = DoubleVar()
        lumEntry = Entry(gammaFrame,textvariable=lVal, validate='key', bg='#FFFDD0')
        lumEntry.grid(row=3,column=2)


        units = StringVar()
        units.set('nw')
        unitsDropdown = OptionMenu(gammaFrame, units, *['\u00B5'+'w','nw','pw'])
        unitsDropdown.grid(row=3, column=3)
        # Press this button to create psychopy window and record luminance values
        dataLabel = Button(gammaFrame,text="Begin calibration",padx=10, command= lambda: beginCal())
        dataLabel.grid(row=3,column=4)

        #Press this button to change gamma without calibration
        gammaLbl = Label(gammaFrame,text='Gamma for {monitor}'.format(monitor=self.stimMonitorSelection.get()), padx=10)
        gammaLbl.grid(row=5, column=1)
        gVal = DoubleVar()
        gVal.set(self.experiment.gamma)
        gammaEntry = Entry(gammaFrame,textvariable=gVal,bg='#FEC47F')
        gammaEntry.grid(row=5,column=2)
        gammaButton = Button(gammaFrame,text='Set gamma', padx=4, command= lambda: monitors.Monitor(self.stimMonitorSelection.get()).setGamma(gVal.get()))
        gammaButton.grid(row=5, column=3)

        self.luminanceValues = []
        def beginCal():
            # Initiate monitor window and GUI for collection of luminance values
            gammaLbl.grid_remove()
            gammaEntry.grid_remove()
            gammaButton.grid_remove()

            def gcloser():
                self.gammaWin.close()
                calibWindow.destroy()

            lumEntry.delete(0,END)
            pixelEntry.delete(0,END)
            pixelEntry.insert(0,-1)
            currPix = -1
            self.pixVals = []
            step_size = steps.get()
            self.gammaWin = visual.Window(screen = self.stimScreenSelection.get(),fullscr=True, color = (-1, -1, -1), monitor = monitors.Monitor(self.stimMonitorSelection.get()))
            calibWindow.protocol('WM_DELETE_WINDOW',gcloser)
            # Set up iterator of pixel values list
            for i in range(int(2/step_size)):
                currPix+=step_size
                currPix = round(currPix,2)
                if self.pixVals.count(currPix) == 0:
                    self.pixVals.append(currPix)
            # Button to iterate through pixel values on each press
            self.pixValsIter = iter(self.pixVals)
            nextButton = Button(gammaFrame,text='Next Pixel Value',padx=10,command= lambda: nextLum())
            nextButton.grid(row=4, column=4)

            def nextLum():
                # Iterate through pixel values to set monitor Window
                lumVal = lVal.get()
                #check if input is number to avoid goofs
                def is_number(str):
                    try:
                        float(str)
                    except Exception as e:
                        return False
                    else:
                        return True

                if lumVal == '' or not(is_number(lumVal)):
                    return
                counts = [0,0,0]
                try:

                    if units.get() == '\u00B5'+'w':
                        lumVal *= 10**-6
                        counts[0] += 1
                    elif units.get() == 'nw':
                        lumVal *= 10**-9
                        counts[1] += 1
                    elif units.get() == 'pw':
                        lumVal *= 10**-12
                        counts[2] += 1

                    self.luminanceValues.append(lumVal)
                    pixVal = next(self.pixValsIter)
                    lumEntry.delete(0,END)
                    pixelEntry.delete(0,END)
                    pixelEntry.insert(0,pixVal)
                    self.gammaWin.color = (pixVal, pixVal, pixVal)
                    self.gammaWin.flip()
                except Exception as e:
                    self.gammaWin.close()
                    nextButton.destroy()
                    self.pixVals.insert(0,-1)

                    #Bring back gamma setter
                    gammaLbl.grid()
                    gammaEntry.grid()
                    gammaButton.grid()

                    # Normalize pixVals
                    normalize = lambda arr: [(x-min(arr))/(max(arr)-min(arr)) for x in arr]
                    reduce = lambda arr,m: [x/(10**-m) for x in arr]
                    pix_inputs = normalize(self.pixVals)
                    # Reduce luminances by most common magnitude. This is because GammaCalculator is more tuned to candela/m^2, and not wattage, like our photometer. Perhaps gamma is not as accurate?
                    count_index = counts.index(max(counts))
                    if count_index == 0:
                        self.luminanceValues = reduce(self.luminanceValues,6)
                    elif count_index == 1:
                        self.luminanceValues = reduce(self.luminanceValues,9)
                    else:
                        self.luminanceValues = reduce(self.luminanceValues,12)

                    # Calculate gamma with normalzed pixels and measured luminances
                    gcalc = monitors.GammaCalculator(inputs=pix_inputs,lums=self.luminanceValues,eq=1)
                    print('---> Done with luminance value collection. Gamma of {gamma} will be set for {monitor}'.format(gamma=gcalc.gamma,monitor=self.stimMonitorSelection.get()))
                    # Set gamma to monitor
                    self.calGamma = gcalc.gamma
                    monitors.Monitor(self.stimMonitorSelection.get()).setGamma(gcalc.gamma)
                    gVal.set(self.calGamma)
                    gammaEntry.delete(0,END)
                    gammaEntry.insert(0,gcalc.gamma)
                    self.stimCalibrationBtn.config(text= '\u03B3 is {g}'.format(g=round(gcalc.gamma,5)))
                    self.setConfigFile()

    # A method to set the warp file from the 'Browse' button in the options menu above
    def findWarpFiletoSave(self, window, entry):
        self.experiment.warpFileName = tkfd.askopenfilename()
        window.attributes('-topmost', True)
        entry.delete(0,END)
        entry.insert(0,self.experiment.warpFileName)


    def applyExperimentChanges(self):
        ''' Execute experiment changes when the apply or apply and save button is pressed'''
        # set stimulus window
        self.experiment.stimMonitor = self.stimMonitorSelection.get()
        self.experiment.fullscr = self.stimFullScreenSelection.get() == 1
        self.experiment.screen = self.stimScreenSelection.get()
        self.experiment.gamma = self.calGamma
        if self.calGamma == 2.0:
            print('***Gamma for monitor set to default value (2.0). Run gamma calibration to load true gamma.')

        # information window
        self.experiment.useInformationMonitor = self.informationUseSelection.get() == 1
        self.experiment.informationMonitor = self.informationMonitorSelection.get()
        self.experiment.informationFullScreen = self.informationFullScreenSelection.get() == 1
        self.experiment.informationScreen = self.informationScreenSelection.get()

        # experiment
        self.experiment.userInitiated = self.userInitSelection.get() == 1
        try:
            self.experiment.angleOffset = float(self.angleOffsetSelection.get())
        except:
            print('***Could not update Angle Offset value. Input type was probably not convertible to a float')

        self.experiment.writeTTL = self.writeTtlSelection.get()
        self.experiment.ttlBookmarks = self.ttlBookmarksSelection.get() == 1
        portSelection = self.ttlPortSelection.get()
        if portSelection in ['No Available Ports', '', None]:
            self.experiment.writeTTL = 'None' #reset write ttl feature to not active
            self.writeTtlSelection.set('None') #reset option box to reflect that you're not writing
            self.experiment.ttlPort = 'No Available Ports' #set the name of the port
        else:
            self.experiment.ttlPort = portSelection #set the name of the port


        self.experiment.useFBO = self.FBObjectSelection.get() == 1
        self.recompileExperiment = self.recompileSelection.get() == 1
        self.experiment.timingReport = self.timingReportSelection.get()==1

        print('\n--> New experiment settings have been applied')


    def setConfigFile(self):
        '''
        Saves applied experiment changes to JSON object that will be stored in src directory
        '''

        configDict = {
            "stimWindow": {
                "stimMonitor": self.stimMonitorSelection.get(),
                "fullscr": self.stimFullScreenSelection.get() == 1,
                "screen": self.stimScreenSelection.get(),
                "gamma": self.calGamma
            },
            "infoWindow": {
                "useInformationMonitor": self.informationUseSelection.get() == 1,
                "informationMonitor": self.informationMonitorSelection.get(),
                "informationFullScreen": self.informationFullScreenSelection.get() == 1,
                "informationScreen": self.informationScreenSelection.get()
            },
            "experiment": {
                "userInitiated": self.userInitSelection.get() == 1,
                "angleOffset": self.angleOffsetSelection.get(),
                "writeTTL": self.writeTtlSelection.get(),
                "ttlBookmarks": self.ttlBookmarksSelection.get(),
                "ttlPort": self.ttlPortSelection.get(),
                "useFBO": self.FBObjectSelection.get() == 1,
                "warpFileName": self.experiment.warpFileName,
                "timingReport": self.timingReportSelection.get()==1
            }
        }

        portSelection = configDict['experiment']['ttlPort']
        if portSelection in ['No Available Ports', '', None]:
            configDict['experiment']['writeTTL'] = False
            configDict['experiment']['ttlPort'] = 'No Available Ports'

        #Once Dictionary is filled with preferences it can be converted to JSON and saved

        with open("configOptions.json", 'w') as f:
            json.dump(configDict,f, indent=4)

        self.applyExperimentChanges()
        print('\n--> Changes to experiment settings have also been saved.')


    def editProtocol(self, e=0, calledByCopy = (False, 0)):
        '''
        Opens a new window in which the user can edit certain 'editable' properties
        of the selected protocol

        e is a placehold in case this function is called by a double left click
        
        calledByCopy is a tuple. If the first value is True then it means this function was called by the copy protocol option in the quick menu box. In that case, use the second value of the tuple to determine the selected index. Otherwise, ignore this variable and simly use the curselection index from the experimentSketchBox
        '''

        # get information about the selected protocol
        if calledByCopy[0]:
            selectedIndex = calledByCopy[1]
        else:
            selectedIndex = self.experimentSketchBox.curselection()[0]
            
        selectedName = self.experimentSketch[selectedIndex][0]
        selectedProtocol = self.experimentSketch[selectedIndex][1]

        # open a new tkinter window to display all properties
        editWindow = Toplevel(root)
        editWindow.title('Edit ' + selectedName +
                         ' at Index ' + str(selectedIndex+1))
        editFrame = Frame(editWindow)
        editFrame.pack(fill="both", expand=True)

        # grab the properties that the user can edit
        allProperties = vars(selectedProtocol)
        propNames = list(allProperties.keys())
        propNames.sort()
        propNamesEditable = []
        propVals = []
        propTypes = []
        entries = []
        for i, prop in enumerate(propNames):
            if prop.startswith('_'):
                # skip private properties that are set by the object itself
                # AS A RULE, THE ONLY DATA TYPES THAT SHOULD BE EDITABLE ARE LISTS,
                # NUMBERS (e.g. float, int), AND STRINGS
                continue

            propNamesEditable.append(prop)

            propVal = allProperties[prop]
            propVals.append(propVal)
            propType = type(propVal)

            # if property type is list you need to figure out what it is a list of
            # (e.g. list of strings). If it is an empty list the default behavior
            # is for it to become a list of strings.
            if propType == list:
                if len(propVal) > 0:
                    subType = type(propVal[0])
                else:
                    subType = type('string')
                propType = (propType, subType)

            propTypes.append(propType)

            label = Label(editFrame, text=prop)
            label.grid(row=i, column=1)

            entry = Entry(editFrame)
            entry.insert(END, str(propVal))
            entry.grid(row=i, column=2)

            entries.append(entry)

            typeLabel = Label(editFrame, text=str(propType))
            typeLabel.grid(row=i, column=3)

        updateDict = {'propNamesEditable': propNamesEditable,
                      'propTypes': propTypes, 'entries': entries}

        # show the estimated time for this particular protocol at the bottom of the window
        protocolRounded_minutes, protocolRemainingSeconds = secondsToMinutesAndSeconds(
            selectedProtocol.estimateTime())
        self.protocolEstimatedTimeLabel = Label(editFrame, text='Estimated Time: ' + str(
            protocolRounded_minutes) + 'm ' + str(protocolRemainingSeconds) + 's')
        self.protocolEstimatedTimeLabel.grid(row=i + 1, column=2)

        buttonGrid = Frame(editFrame)
        buttonGrid.grid(row=i + 2, column=2)

        #make the apply changes button a property so that it can be accessed by self.applyPropertyChanges() function in order to update the button color if validations aren't passed
        self.applyChangesButton = Button(buttonGrid, text='Apply Changes',
                                    command=lambda: self.applyPropertyChanges(selectedIndex, selectedProtocol, updateDict))
        self.applyChangesButton.grid(row=1, column=1)
        closeButton = Button(buttonGrid, text='Close Window',
                             command=lambda: editWindow.destroy())
        closeButton.grid(row=1, column=2)


    def applyPropertyChanges(self, selectedIndex, selectedProtocol, updateDict):
        '''
        Updates the selected protocol with new properties that are sotred in
        update dict

        inputs:
            - selectedIndex = index of selected protocol in self.experimentSketch
            - selectedProtocol = the potocol object that has been selected
            - updateDict = update instructions for new attribute values
        '''
        pnameWithSpaces = self.experimentSketch[selectedIndex][0]
        copyOfSelectedProtocol = copy.deepcopy(selectedProtocol)
        
        updateNames = updateDict['propNamesEditable']
        userEntries = updateDict['entries']
        updateTypes = updateDict['propTypes']

        # Reassign each property that the user may have changed
        for i, val in enumerate(userEntries):
            try:
                entryString = val.get()
                convertToType = updateTypes[i]
                propName = updateNames[i]

                if convertToType == str:
                    convertedValue = entryString
                elif convertToType == int:
                    convertedValue = int(entryString)
                elif convertToType == float:
                    convertedValue = float(entryString)
                elif convertToType == bool:
                    convertedValue = entryString == 'True'
                # will be a tuble when you have a LIST of something
                elif type(convertToType) == tuple:
                    # first and last are '[' and ']'
                    splitList = entryString[1:-1].split(',')
                    # second index in the tuple tells you what it's a list of (e.g. list of strings)
                    if convertToType[1] == str:
                        convertedValue = [el.strip()
                                          for el in splitList if el != '']
                    elif convertToType[1] == int:
                        convertedValue = [int(el.strip())for el in splitList]
                    elif convertToType[1] == float:
                        convertedValue = [float(el.strip())
                                          for el in splitList]

                setattr(selectedProtocol, propName, convertedValue)
            except:
                print('***Update Failure for property with name ' + updateNames[i]
                      + ' Multiple problems may cause this error. Recommend checking input syntax and type for property update value')
        
         #check any validations that are needed for the current stimulus type
        tf, errorMessage = selectedProtocol.validatePropertyValues()
        if not tf:
             print('\n***Update Failure. Could not update this stimulus because validations on property assignments were not passed. This came with the following error message:')
             print('VALIDATION ERROR: ' + errorMessage)
             
             #place the old protocol back into the experiment sketch
             self.experimentSketch[selectedIndex] = (
                 pnameWithSpaces, copyOfSelectedProtocol)
             
             self.applyChangesButton.configure(bg=_from_rgb((200, 150, 150)))
             return
         
        self.applyChangesButton.configure(bg=_from_rgb((240, 240, 240)))
         
        # put the object back into the experiment sketch
        self.experimentSketch[selectedIndex] = (
            pnameWithSpaces, selectedProtocol)

        # reload the experiment sketch list box
        self.updateExperimentSketch()
        
        # update time estimation in the edit window
        protocolRounded_minutes, protocolRemainingSeconds = secondsToMinutesAndSeconds(
            selectedProtocol.estimateTime())
        self.protocolEstimatedTimeLabel.configure(text='Estimated Time: ' + str(
            protocolRounded_minutes) + 'm ' + str(protocolRemainingSeconds) + 's')
        
        print('Stimulus was successfully updated')

    def removeProtocol(self):
        '''
        Remove the selected protocol from the experiment sketch
        '''
        try:
            selectedIndex = self.experimentSketchBox.curselection()[0]
            del self.experimentSketch[selectedIndex]
        except:
            print('\n***Invalid remove request. Select a protocol to remove first')

        self.updateExperimentSketch()


    def updateExperimentSketch(self):
        '''
        Updates the list box that displays the order in which protocols will run
        '''
        self.saveExperimentButton.configure(bg=_from_rgb((200, 100, 100)))
        # remove all previously displayed items
        self.experimentSketchBox.delete(0, 'end')

        # reset the list box with the new list
        estimatedTime_seconds = 0
        for i, p in enumerate(self.experimentSketch):
            name = p[0]
            suffix = p[1].suffix  # suffix is a property of the protocol
            estimatedTime_seconds += p[1].estimateTime()

            # Display the protocol name (with spaces) and the suffix (if it has been assigned)
            if suffix == '_' or suffix.strip() == '':
                displayName = name
            else:
                displayName = name + suffix

            self.experimentSketchBox.insert(i, displayName)

        self.experimentSketchBox.pack()

        self.protocolIndexField.delete(0, END)
        self.protocolIndexField.insert(END, str(len(self.experimentSketch)+1))

        rounded_minutes, remainingSeconds = secondsToMinutesAndSeconds(
            estimatedTime_seconds)
        self.estimatedTimeLabel.configure(
            text='Estimated Time: ' + str(rounded_minutes) + 'm ' + str(remainingSeconds) + 's')

        # bind double click left button to edit the current field
        self.experimentSketchBox.bind('<Double-Button-1>', self.editProtocol)
        # bind single right click to getting the updating the protocol index field
        self.experimentSketchBox.bind('<Button-3>', self.changeProtocolIndex)


    def compileExperiment(self):
        '''
        Generates experiment.protocolList based off the protocol objects listed
        in self.experimentSketch.

        experiment.protocolList is required to run experiment.activate()
        '''
        print('\n--> Clearing pre-existing experiments...')
        # clear the protocolList in case it has any previous data
        self.experiment.protocolList = []

        print('--> Assembling new experiment...')
        for p in self.experimentSketch:
            protocolObject = p[1]
            self.experiment.addProtocol(protocolObject)


    def saveExperiment(self):
        '''
        save the experiment information
        '''
        if self.recompileExperiment:
            self.compileExperiment()
        else:
            print('--> Bassoon is saving the previously compiled experiment...')

        expfname = tkfd.asksaveasfilename(defaultextension='.experiment',
                                          filetypes=[
                                              ("Experiment Files", '*.experiment')],
                                          title="Save Experiment")

        if expfname == '':
            print('--> Save was ABORTED. Try saving again from the Bassoon GUI or console. Recompile should be set to False in the options menu in order to keep current data...')
            return

        # set wins to None type because they may still be running processes which will prevent pickling
        self.experiment.win = None
        self.experiment.informationWin = None
        with open(expfname, 'wb') as f:
            pickle.dump(self.experiment, f)

        # save a json file as well that can be read in matlab
        jsonfname = expfname[0:-11] + '.json'
        jsonDict = vars(self.experiment)
        jsonDict['protocolList'] = [p[0] for p in jsonDict['protocolList']]
        for p in jsonDict['loggedStimuli']:
            p.pop('_portObj', None)


        try:  # LOOK INTO WHY THESE COMMANDS THROW AN ERROR SOMETIMES... MIGHT HAVE TO DO WITH WHEN AN EXPERIMENT IS RELOADED AFTER BEING RUN ONCE
            jsonDict['experimentStartTime'] = jsonDict['experimentStartTime'].strftime(
                "%D %H:%M:%S")
            jsonDict['experimentEndTime'] = jsonDict['experimentEndTime'].strftime(
                "%D %H:%M:%S")
        except:
            pass
        with open(jsonfname, 'w') as f:
            json.dump(jsonDict, f)

        now = datetime.now()
        print('--> Save succesful. Time: ', now.strftime("%D %H:%M:%S"))
        print('--> .experiment and .json files saved at ' +
              expfname[0:-11] + '.*')
        try:
            self.saveExperimentButton.configure(bg=_from_rgb((100, 200, 100)))
        except:
            print('It looks like the Bassoon GUI is not accessable... if it has already closed then you can ignore this message')
            

    def runExperiment(self):
        '''
        Execute the psychopy experiment
        '''
        # assemble the experiment
        self.compileExperiment()

        self.recompileExperiment = False

        # add all protocol objects to the experiment
        print(' \n--> Preparing to run experiment. Bassoon will become tacet.')

        root.withdraw()  # hide bassoon while the experiment is running
        print('--> Tacet!')
        print('--> Experiment is now live! If available, use the information window for further assistance. Good luck.')

        self.experiment.experimentStartTime = datetime.now()  # write down start time
        self.experiment.activate()  # run the experiment
        self.experiment.experimentEndTime = datetime.now()  # write down end time

        try:
            print('\n--> The experiment has ended. Please save.')
            # pass recompile = False becasue you want to save the experiment that you just ran, not a new one
            self.saveExperiment()

        except:
            print('\n***NOTICE: THE PRECEEDING EXPERIMENT WAS NOT SAVED. MANUALLY SAVE BEFORE PROCEEDING OR THE EXPERIMENT WILL BE LOST.' +
                  '\n--> Invoke app.recompileExperiment = False; app.saveExperiment() to save the experiment.' +
                  '\n--> Alternatively, the experiment object is located at app.experiment. However, this object may not be immediately pickalable without invoking \'app.experiment.win = None\' and \'app.experiment.informationWin = None\'')

        print('\n\nBassoon is ready to play again!')
        root.deiconify()


#########HELPERS##########
def _from_rgb(rgb):
    '''
    translates an rgb tuple of ints to a tkinter friendly color code
    '''
    return "#%02x%02x%02x" % rgb


def secondsToMinutesAndSeconds(seconds):
    '''
    Given a number specifying a time in seconds, this function returns the
    equivalent number of minutes and seconds

    Parameters
    ----------
    seconds : Number. Specifies time in seconds

    Returns
    -------
    roundedMinutes : integer of total minutes
    remainingSeconds: integer of remaining seconds in addition to roundedMinutes
    '''
    minutes = seconds/60
    rounded_minutes = math.floor(minutes)
    remainingSeconds = int((minutes-rounded_minutes)*60)

    return rounded_minutes, remainingSeconds


##############################################################################
root = Tk()  # full function = tk.Tk()
root.geometry('400x600')
#root.iconbitmap(r'images\bassoonIcon.ico')
app = Bassoon(root)

root.mainloop()
root.destroy()


# Example of how to load experiments without opening the GUI:
# e = experiment() #load an experiment object
# b = MovingBar() #load a protocol subclass (i.e. a stimulus)
# b.stimTime = 3 #change stimulus attributes as you see fit
# e.addProtocol(b) #Add the modified stimulus to the experiment

# e.stimMonitor = 'testMonitor' #modify experiment attributes as you see fit
# e.useInformationMonitor = True
# e.informationMonitor = 'testMonitor'
# e.activate() #activate the experiment
