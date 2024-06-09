# -*- coding: utf-8 -*-
"""
Created on Fri Jul  9 17:24:45 2021

@author: mrsco
"""
from psychopy import core, visual, data, event, monitors
import time
import random, math

class protocol():
    def __init__(self):
        self.suffix = '_' #suffix for the protocol name, begin with _
        self.userInitiated = False #determines whether a key stroke is needed to initiate the protocol. Will be set to the corresponding experiment value if not updated by the user
        
        self._stimulusStartLog = [] #list of time stamps marking the start of each epoch
        self._stimulusEndLog = [] #list of time stamps marking the end of each epoch
        self._pauseTimeLog = []
        
        self.randomSeed = random.random()
        
        self.tagList = [] #list of tags for the protocol
        
        self._estimatedTime = 0.0 #estimated time in seconds that this stimulus will take. There should be a corresponding function self.estimateTime() that sets this number
        
        self._numberOfEpochsStarted = 0
        self._numberOfEpochsCompleted = 0 #counts the number of epochs that have actually occured
        
        self._portName = '' #name of the TTL port if in use. Implemented 
        self._timesTTLFlipped = 0 #counts the number of TTL flips, used for sustained mode only
        self._timesTTLFlippedBookmark = 0 #counts the number of TTL flips during bookmark (sustained mode with bookmarking only)
        
        self._userPauseCount = 0 #counts the number of times the user initiated a pause in the middle of the stimulus
        self._userPauseDurations = [] #list of amount of time (in seconds) that each pause lasted for
        
        self._completed = -1 # -1 indicates stimulus never ran. 0 indicates stimulus started but ended early. 1 indicates stimulus ran to completion
        
        self._timingReport = False #bool, inhereted from experiment parameters. Indicates whether the user wants to print a timing report for each stimulus (usually to determine if frames are being dropped)
        
    def validatePropertyValues(self, tf = True, errorMessage = ''):
        '''
        Validates the property values for select protocols. It does this by looking for an internal validation function within the protocol subclass called "internalValidation()". If this function does not exist, the validations are automatically passed.

        Returns:
            tf - bool value, true if validations are passed, false if they are not
            errorMessage - string, message to be displayed in validations are not passed
        '''
        internalValidation = getattr(self, "internalValidation", None)
        if not callable(internalValidation):
            return tf, errorMessage
        
        tf, errorMessage = self.internalValidation()
        
        return tf, errorMessage

    def estimateTime(self):
        '''
        estimateTime place holder. Should be overriden in subclass
        '''
        return 0
        
    
    def getFR(self, win):
        '''
        Determine the frame rate of the win object (e.g. stimulus monitor) and calculate number of frames and total time for each segment of the stimulus
        '''
        
        self._FR = win.getActualFrameRate()
        
        #On rare occasions (depending on the monitor) there appears to be a timing issue with winl.getActialFrameRate().
        #In such cases, you can keep querying until you get a numerical value other than None
        #I've set a stop here after 1000 queries, which seems sufficient to prevent this error and avoids an infinite loopq
        if self._FR is None:
            count = 0
            while self._FR is None and count < 1000:
                self._FR = win.getActualFrameRate()

        self._preTimeNumFrames = round(self._FR*self.preTime)
        self._stimTimeNumFrames = round(self._FR*self.stimTime)
        self._tailTimeNumFrames = round(self._FR*self.tailTime)

        self._actualPreTime = self._preTimeNumFrames * 1/self._FR
        self._actualStimTime = self._stimTimeNumFrames * 1/self._FR
        self._actualTailTime = self._tailTimeNumFrames * 1/self._FR
        
    def getPixPerDeg(self, stimMonitor):
        '''
        determine the pixels per degree for the stimulus monitor
        '''
        mon = monitors.Monitor(stimMonitor.name)
        eyeDistance = mon.getDistance()
        numPixelsWide = mon.currentCalib['sizePix'][0]
        cmWide = mon.currentCalib['width']
        totalVisualDegrees = 2*math.degrees(math.atan((cmWide/2)/eyeDistance))
        return numPixelsWide/totalVisualDegrees
    
    def showInformationText(self, stimWin, txt):
        '''
        update the information window
        '''
        if self._informationWin[0]:
            win = self._informationWin[1]
        else:
            win = stimWin
        
        informationalText = visual.TextStim(
                                    win = win, 
                                    text = txt)

        informationalText.draw()
        win.flip()

    def checkQuitOrPause(self):
        '''
        Checks if user wants to quit early during a stimulus or pause the stimulus. Press 'q' key to quit early. Press 'p' to pause the stimulus''
        '''
        allKeys = event.getKeys() #check if user wants to quit early
        if len(allKeys)>0:
            if 'q' in allKeys:
                self._stoppedEarly = 1
                print('*** Quiting stimulus early')
                return 1
            elif 'p' in allKeys:
                self._userPauseCount += 1
                print('*** STIMULUS HAS PAUSED. Press any key to resume')
                startTime = time.time()
                event.waitKeys() #wait for key press to resume
                endTime = time.time()
                pauseTime = endTime - startTime
                print('*** Resuming Stimulus. Total pause time was %s seconds' % pauseTime)
                self._userPauseDurations.append(pauseTime)
                return 0
            
        return 0
            
    
    def sendTTL(self, bookmark = False):
        '''
        sends ttl pulse during experiment if the setting is turned on TTL pulse or sustained can be selected. If pulse is turned on, this only executes during a protocol, but not before.
        '''
        if self.writeTTL == 'Pulse':
                try:
                    self._portObj.write(0X4B)
                except:
                    print('***WARNING: TTL Pulse Failed***')
        
        elif self.writeTTL == 'Sustained':
            if bookmark:
                self._timesTTLFlippedBookmark += 1
            else:
                self._timesTTLFlipped += 1
                
            if self._TTLON: #IF TTL is ON, turn it OFF
                self._portObj.rts = True #'True' turns TTL off on picolo
                self._TTLON = False
            else: # If TTL is OFF, turn it ON
                self._portObj.rts = False #'False' turns TTL ON on picolo
                self._TTLON = True
        return
    
    
    def burstTTL(self, win):
        '''
        sends a burst of TTL pulses at the start of a stimulus when the the TTL port is in pulse mode. As of 10/29/2023 this appears to only be implemented for checkerboard receptive field and flash grid. The stereotyped burst is 20 TTL pulses at frame rate, wait 0.2 seconds, and 20 more TTL pulses at frame rate
        '''
        if self.writeTTL != 'Pulse':
            return
        
        for i in range(20):
            self.sendTTL()
            win.flip()
            
        core.wait(0.2)
        
        for i in range(20):
            self.sendTTL()
            win.flip()
        
        return
    
    
    def reportTime(self, displayName):
        '''
        Prints a timing report for each stimulus when the experiment settings indicate to do so. This is primarily used for diagnostic purposes or when designing new stimuli.
        
        inputs:
            - displayName: string that shows the name of the current stimulus
        '''
        
        #make sure the stimulus was fully completed. If it was not, the timing report is not generated
        if not self._completed:
            print(f"*** ALERT: The timing report for {displayName} could not be generated because the protocol was not run to completion. Retry without terminating the protocol early.\n")
            return
        
        
        #Calculate the timing metrics
        #the start and stop time of each epoch are calculated and reported to the user. Usually, this does not include the interstimulus interval.
        allTimes = [self._stimulusEndLog[i]-self._stimulusStartLog[i] for i in range(len(self._stimulusEndLog))]
        totalTime = self._stimulusEndLog[-1] - self._stimulusStartLog[0]
        percentDifference = 100*self._estimatedTime/totalTime
        print(f"-----------Timing Report Summary for {displayName}--------------")
        print("\nTime Elapsed Per Epoch:")
        
        for i, time in enumerate(allTimes):
            print(f"Epoch {i + 1}: {time:.2f} seconds")
            
        print('(note that reported epoch times typically do not include interstimulus intervals. See the script for the specific protocol for more information)\n')
        
        #then, the total elapsed time for the stimulus is compared to the expected elapsed time
        print(f"Total Time Elapsed for this Stimulus: {totalTime:.2f} seconds")
        print(f"Expected Time Elapsed for this Stimulus: {self._estimatedTime:.2f} seconds")
        
        #a frame rate calculation is made using the total and expected elapsed time
        print("\nFrame Rate Information:")
        print(f"Expected Frame Rate: {self._FR} Hz")
        print(f"Actual Frame Rate (percentage of expected): {percentDifference:.2f}%")
        
        #check if there were any manual pauses. If so, tell the user just in case
        if self._userPauseCount > 0:
            print('\n*** Note: Be aware that {self._userPauseCount} user pauses were detected during this stimulus, which will affect the timing report.')
        print("---------------------------------------------\n")
        
        return

    
    def printProgressBar(self, iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
        '''
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
            printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
        
        adapted from: https://stackoverflow.com/questions/3173320/text-progress-bar-in-terminal-with-block-characters By @Greenstick
        '''
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
        # Print New Line on Complete
        if iteration == total: 
            print()