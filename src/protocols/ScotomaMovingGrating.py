# -*- coding: utf-8 -*-
"""
Created on Sat May  4 00:58:21 2024

Grating moves across the screen as an overlaid scotoma mask changes density

@author: mrsco
"""
from protocols.protocol import protocol
from psychopy import core, visual, data, event, monitors
import serial, random, math
import numpy as np

class ScotomaMovingGrating(protocol):
    def __init__(self):
        super().__init__()
        self.protocolName = 'ScotomaMovingGrating' #in the Scotoma Moving Grating stimulus, there is a drifting grating pattern that is progressively covered by a grid of "scotomas" (overlaid on top of the grating). The stimulus consists of up to 7 segments:   1) pretime: the grating is visible and static, with the initial scotoma density overlaid (defined by the scotoma start fraction),   2) bookend 1: the grating starts to move, but the scotomas do not change (again, the initial scotoma density is overlaid, but it is static),   3) growth/decay period 1: the grating continues to move, and the scotomas start to dynamically change in number from their start fraction to their end fraction (if scotomaReverse is set to False, skip ahead to segment 6),   4) bookend 2 (occurs only when scotomaReverse is set to True): the scotomas have reached their end fraction and are now static again while the grating continues to move,    5) growth/decay period 2 (occurs only when scotomaReverse is set to True): the scotomas start to dynamically change again, this time going from the end fraction to the start fraction value,   6) bookend 3: the scotomas now stop changing again, but the grating continues to move,   7) tailtime: the grating is visible and static, with the final scotoma density overlaid (final scotoma densitiy is equal to the scotomaEndFraction if scotomaReverse is False and the scotomaStartFraction if scotomaReverse is True).      The scotoma start fraction can be less than or greater than the end fraction. If if it is less than the end fraction, then scotomas will start out by appearing on the screen. If it is greater than the end fraction, then scotomas will start out by disappearing on the screen. The order of scotoma appearance is pseudorandom. You visualize this stimulus by following this link, where the start fraction is 0, then end fraction is 1, and scotomaReverse is set to True: https://youtu.be/9pvIeY91nvk
        
        #grating parameters
        self.gratingColor = [1.0, 1.0, 1.0] #color of the grating (in RGB).-1.0 equates to 0 and 1.0 equates to 255 for 8 bit colors.
        self.gratingContrast = 1.0 #Sets the contrast of the grating by multiplying by the the grating color.
        self.meanIntensity = 0.0; #The mean intensity of the grating. This value should be between -1 and 1.0, where 0.0 is "middle gray"
        self.spatialFrequency = 0.15 #cycles per degree - the spatial frequency of the grating
        self.gratingTexture = 'sin' #The pattern of the grating. This can be 'sin', 'sqr', 'saw', 'tri', etc. Look at Psychopy gratingstim object for more information: https://www.psychopy.org/api/visual/gratingstim.html#psychopy.visual.GratingStim.tex 
        self.speed = 10.0 #degrees per second - the speed at which the grating moves
        self.orientations = [90.0] #degrees - a list of directions that the grating will move in. The total number of epochs is equal to the number of orientations times the number of stimulus repetitions.
        self.backgroundColor = [0.0, 0.0, 0.0] #background color of the screen (in RGB). -1.0 equates to 0 and 1.0 equates to 255 for 8 bit colors. For this stimulus, the background is typically only seen between epochs.
        
        #scotoma parameters
        self.scotomaStartFraction = 0.0 #Fraction of pixels that start as a scotoma. This number can be between 0.0 and 1.0.
        self.scotomaEndFraction = 1.0 #Fraction of pixels that end as a scotoma after one growth/decay period. This number can be between 0.0 and 1.0
        self.scotomaOpacity = 1.0 #The opacity of the scotomas. 1.0 is fully opaque, 0.0 is fully transparent
        self.scotomaReverse = True #bool - True means that the scotomas will go from start to end and then end to start again. False means they will only go from start to end (press the information button on protocolName for more insight).
        self.scotomaGrowthTime = 80.0 #seconds - the amount of time that one growth/decay period takes.
        self.scotomaBookendTime = 10.0 #seconds - the amount of time that each bookend takes. During the bookends, the grating moves but the scotomas do not change. All bookends must be the same length. There are a maximum of three bookends per epoch: Once immediately after the pretime, once immediately before the tail time, and (if scotomaReverse is set to True) once between the first and second growth/decay times.
        self.scotomaGrowth = 'lin' #Sets the pattern of scotoma growth. Currently only 'lin' is supported for linear growth
        self.scotomaSize = 0.67 #degrees - The size of the scotomas (height and width). Scotomas will be square, such that height == width
        self.scotomaColor = [0.0, 0.0, 0.0] #The color of the scotomas (in RGB).-1.0 equates to 0 and 1.0 equates to 255 for 8 bit colors.
        
        self.stimulusReps = 3 #number of repetitions of the stimulus. The total number of epochs is equal to the number of orientations times the number of stimulus reps.
        self.preTime = 20.0 #seconds - the number of seconds before the first bookend, when the grating starts moving. During this time, a static grating with the scotoma start fraction of scotomas overlaid appears on the screen.
        self.stimTime = 0.0 #seconds - the total time that the grating moves for. This number is calculated during run time and should not be edited directly. It is listed here as a dummy variable because it is required by the getFR method in protocol.py
        self.tailTime = 20.0 #seconds - the number of seconds after the last bookend. During this time a static grating with the scotoma start or end fraction overlaid appears on the screen.
        self.interStimulusInterval = 1.0 #seconds - the wait time between each epoch. The background color is displayed during this time
        self._angleOffset = 0.0 # reassigned by the experiment in most cases


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
        if self.scotomaStartFraction > 1 or self.scotomaStartFraction < 0 or self.scotomaEndFraction > 1 or self.scotomaEndFraction < 0:
            tf = False
            errorMessage.append('The scotoma start and end fractions must be a value between 0 and 1. If set to 1, all pixels will be blanked. If set to 0, no pixels will be blanked. If set to 0.5, half of the pixels will be blanked.')
        
        if self.scotomaGrowth != 'lin':
            tf = False
            errorMessage.append('The Scotoma Growth parameter must be set to "lin". Other growth options will be supported in future versions.')
        
        if self.scotomaOpacity > 1 or self.scotomaOpacity < 0:
            tf = False
            errorMessage.append('Scotoma Opacity must be between 0.0 and 1.0. 1 is fully opaque, 0 is transparent.')
            
        if self.stimTime != 0:
            self.stimTime = 0
            print('\nNOTE: Stim Time was reset to 0. It will be updated on the fly during run time. Users should not manually change this parameter for the Scotoma Moving Grating stimulus.')
            
        if self.scotomaSize < 0.5:
            print('\nNOTE: Scotoma Size is small. This may slow down the frame rate. If this occurs, increase scotoma size to improve the frame rate')
        
        
        tf, colorErrorMessages = self.validateColorInput()
        errorMessage += colorErrorMessages
         
        return tf, errorMessage


    def estimateTime(self):
        '''
        Estimate the total amount of time that this protocol will take to run
        given the current parameters

        Value is stored as total time in seconds in the property 'self._estimatedTime'
        which is initialized by the protocol superclass.

        returns: estimated time in seconds
        '''
        if self.scotomaReverse:
            st = 3*self.scotomaBookendTime + 2*self.scotomaGrowthTime
        else:
            st = 2*self.scotomaBookendTime + self.scotomaGrowthTime
            
        timePerEpoch = self.preTime + st + self.tailTime + self.interStimulusInterval
        numberOfEpochs = self.stimulusReps * len(self.orientations)
        self._estimatedTime = timePerEpoch * numberOfEpochs #return estimated time for the total stimulus in seconds

        return self._estimatedTime


    def createOrientationLog(self):
        '''
        Generate a random sequence of orientations given the desired orientations

        Desired orientations are specified as a list in self.orientations

        creates self._orientationLog, a list which specifies the orienation
        to use for each epoch
        '''
        orientations = self.orientations
        self._orientationLog = []
        random.seed(self.randomSeed) #reinitialize the random seed

        for n in range(self.stimulusReps):
            self._orientationLog += random.sample(orientations, len(orientations))
            
        return
    
    
    def createScotomaGrowthSequence(self, numScotomasToAdd, numTotalScotomas, scotomaIndices):
        '''
        Builds a sequence of scotoma indices to add or remove from the mask
        
        Inputs:
            - numScotomasToAdd: the total number of scotomas you need to add by the end of the growth sequence. Can be a positive or negative integer. If this number is negative, you'll be taking away scotomas from the mask rather than adding them
            - scotomaIndices: list 1d indices where scotomas have already been filled
            
        Returns:
            - no explicit returns, but creates variables self._newScotomasPerFrame (number of new scotomas to add on each frame) and self._scotomaSequence (list of indices that indicate where to add or take away scotomas in sequence)
        '''
        
        if self.scotomaGrowth == 'lin':
            #First figure out an integer number of scotomas to add on each frame. Consider that you need to add an integer number on each frame, and the frame rate may not divide the growth rate evenly
            meanScotomasAddedPerFrame = numScotomasToAdd / self._numFramesGrowth
            cumulativeScotomasAdded = np.round(np.cumsum([meanScotomasAddedPerFrame for f in range(self._numFramesGrowth)]))
            self._newScotomasPerFrame = np.diff(cumulativeScotomasAdded) #new scotomas per frame is the number of new additions to make on every sequential frame.
            self._newScotomasPerFrame = [int(el) for el in self._newScotomasPerFrame] #convert to list of integers
            self._newScotomasPerFrame = [round(meanScotomasAddedPerFrame)] + self._newScotomasPerFrame
            
        elif self.scotomaGrowth == 'exp':
            #   --- enter code here for exponential growth pattern --- #
            pass
            
        #if adding scotomas:
        if numScotomasToAdd > 0:
            noScotomaIndices = list(set([i for i in range(numTotalScotomas)]) - set(scotomaIndices))
            self._scotomaSequence = np.array(random.sample(noScotomaIndices, numScotomasToAdd)) 

        #if subtracting scotomas:
        if numScotomasToAdd < 0:
            self._scotomaSequence = np.array(random.sample(scotomaIndices, -numScotomasToAdd))
            self._newScotomasPerFrame = [-x for x in self._newScotomasPerFrame]

        if numScotomasToAdd == 0:
            self._scotomaSequence = np.array([0])
        
        self._scotomaSequence = self._scotomaSequence.tolist() # make it a list b/c ndarrays have trouble saving
        
        return
            
    def run(self, win, informationWin):
        '''
        Executes the ScotomaMovingGrating stimulus
        '''
        
        self._completed = 0 #started but not completed

        self._informationWin = informationWin #tuple, save here so you don't have to pass this as a function parameter every time you use it
        
        #update the stim time
        if self.scotomaReverse:
            self.stimTime = 3*self.scotomaBookendTime + 2*self.scotomaGrowthTime
        else:
            self.stimTime = 2*self.scotomaBookendTime + self.scotomaGrowthTime
            
        self.getFR(win)
        self._interStimulusIntervalNumFrames = round(self._FR * self.interStimulusInterval)
        self._actualInterStimulusInterval = self._interStimulusIntervalNumFrames * 1/self._FR

        stimMonitor = win.monitor
        pixPerDeg = self.getPixPerDeg(stimMonitor)

        #Pause for keystroke if the user wants to manually initiate
        if self.userInitiated:
            self.showInformationText(win, 'Stimulus Information: Scotoma Moving Grating\nPress any key to begin')
            event.waitKeys() #wait for key press

        spatialFrequencyCyclesPerPixel = self.spatialFrequency * (1/pixPerDeg)

        grating = visual.GratingStim(
            win,
            size = (win.size[0]*2, win.size[1]*2),
            sf = (spatialFrequencyCyclesPerPixel, None),
            tex = self.gratingTexture,
            contrast = self.gratingContrast,
            color = self.gratingColor,
            )
        
        #create the mask
        winWidthPix = win.size[0]
        winHeightPix = win.size[1]

        scotomaSizePix = int(self.scotomaSize*pixPerDeg) #maybe a slight rounding error here by using int
        
        #specify the x and y center coordinates for each check
        xCoordinates = [x - win.size[0]/2 for x in range(-scotomaSizePix, win.size[0]+scotomaSizePix, scotomaSizePix)]
        yCoordinates = [y - win.size[1]/2 for y in range(-scotomaSizePix, win.size[1]+scotomaSizePix, scotomaSizePix)]
        numTotalScotomas = len(xCoordinates) * len(yCoordinates)
        sizes = [(scotomaSizePix, scotomaSizePix) for i in range(numTotalScotomas)]
       
        self._scotomaCoordinates = []
        colors = []
        for i in range(len(xCoordinates)):
            for j in range(len(yCoordinates)):
                self._scotomaCoordinates.append([xCoordinates[i], yCoordinates[j]])
                
        scotomaMask = visual.ElementArrayStim(
            win,
            nElements = numTotalScotomas,
            elementMask="None",
            elementTex = None,
            xys = self._scotomaCoordinates,
            sizes = sizes,
            colors = self.scotomaColor
            )
        
        random.seed(self.randomSeed) #reinitialize the random seed
        
        mask = np.zeros((numTotalScotomas, 1)) #1 is fully transparent, -1 is fully opaque. Start with a fully transparent mask.
    
        #fill the mask with the number of scotomas needed at the start of the stimulus
        numScotomasStart = round(numTotalScotomas*self.scotomaStartFraction)
        scotomaIndices = random.sample([i for i in range(numTotalScotomas)], numScotomasStart)
        mask[scotomaIndices] = self.scotomaOpacity
            
        scotomaMask.opacities = mask #set the first mask
        
        
        #Now build up a list of which mask locations you want to update on each frame 
        numScotomasEnd = round(numTotalScotomas*self.scotomaEndFraction)
        numScotomasToAdd = numScotomasEnd - numScotomasStart #note, this value can be positive or negative.
            
        self._numFramesGrowth = round(self._FR * self.scotomaGrowthTime) #number of frames overwhich the scotoma will grow
        self._actualScotomaGrowthTime = self._numFramesGrowth * 1/self._FR
        
        self._numFramesBookend = round(self._FR * self.scotomaBookendTime)
        self._actualBookendTime = self._numFramesBookend * 1/self._FR
        
        #create self._scotomaSequence and self._newScotomasPerFrame
        self.createScotomaGrowthSequence(numScotomasToAdd, numTotalScotomas, scotomaIndices)
            
        #create flipped copies of self._scotomaSequence and self._newScotomasPerFrame if you will also be doing a reverse
        if self.scotomaReverse:
            scotomaSequenceReverse = np.flip(self._scotomaSequence)
            newScotomasPerFrameReverse = np.flip(self._newScotomasPerFrame)
        
        #The cover rectangle is drawn on top of the primary grating. It is used
        #to change the mean intensity of the grating when the user desires.
        #If the mean intensity is set to 0, then the cover rectangle is still
        #drawn but with an opacity of 0
        coverRectangle = visual.Rect(
            win,
            size = (win.size[0]*2, win.size[1]*2),
            opacity = 0
            )

        if self.meanIntensity > 0:
            coverRectangle.fillColor = [1, 1, 1]
            coverRectangle.opacity = self.meanIntensity
        elif self.meanIntensity < 0:
            coverRectangle.fillColor = [-1, -1, -1]
            coverRectangle.opacity = -1*self.meanIntensity

        self._numCyclesToShiftByFrame = self.speed*self.spatialFrequency*(1/self._FR)

        self.createOrientationLog()
        
        
        totalEpochs = len(self._orientationLog)
        epochNum = 0
        trialClock = core.Clock() #this will reset every trial
                
        #stimulus loop
        for ori in self._orientationLog:
            grating.ori = -ori - self._angleOffset #flip for coordinate convention: 0 = east, 90 = north, 180 = west, 270 = south
            epochNum += 1
            #show information if necessary
            if self._informationWin[0]:
                self.showInformationText(win, 'Running Scotoma Moving Grating. Current orientation = ' + \
                                         str(ori) + '\n Epoch ' + str(epochNum) + ' of ' + str(totalEpochs))


            #pause for inter stimulus interval
            win.color = self.backgroundColor
            for f in range(self._interStimulusIntervalNumFrames):
                win.flip()
                if self.checkQuitOrPause():
                    return

            #pretime... stationary grating
            self._stimulusStartLog.append(trialClock.getTime())
            self.sendTTL()
            self._numberOfEpochsStarted += 1
            for f in range(self._preTimeNumFrames):
                grating.draw()
                coverRectangle.draw()
                scotomaMask.draw()
                win.flip()
                if self.checkQuitOrPause():
                    return

            
            #stim time
            
            #bookend 1 (grating starts moving before scotomas are added)
            for f in range(self._numFramesBookend):
                grating.phase += self._numCyclesToShiftByFrame
                grating.draw()
                coverRectangle.draw()
                scotomaMask.draw()
                win.flip()
                if self.checkQuitOrPause():
                    return
            
            #first check whether you will be adding or taking away scotomas. Assign the addColor accordingly so that when you update the mask it either places a scotoma or sets the value to transparent
            if numScotomasToAdd > 0:
                addColor = self.scotomaOpacity #scotoma color, used when adding scotomas
            else:
                addColor = 0 #transparent - used when taking away scotomas

            #scotoma growth starts here
            count = 0 
            for f in range(self._numFramesGrowth):
                scotomasToChangeThisFrame = self._scotomaSequence[count:count+self._newScotomasPerFrame[f]]
                count += self._newScotomasPerFrame[f]
                mask[scotomasToChangeThisFrame] = addColor
                scotomaMask.opacities = mask
                grating.phase += self._numCyclesToShiftByFrame
                grating.draw()
                coverRectangle.draw()
                scotomaMask.draw()
                win.flip()
                if self.checkQuitOrPause():
                    return
            
            #middle bookend
            if self.scotomaReverse:
                #pause time before reversal
                for f in range(self._numFramesBookend):
                    grating.phase += self._numCyclesToShiftByFrame
                    grating.draw()
                    coverRectangle.draw()
                    scotomaMask.draw()
                    win.flip()
                    if self.checkQuitOrPause():
                        return
                
                if numScotomasToAdd > 0:
                    addColor = 0 #if you were originally adding scotomas, now you'll take them away
                else:
                    addColor = self.scotomaOpacity #if you were originally taking away scotomas, now you'll add them
                #flip the scotoma sequence and scotomas to change this frame lists
                count = 0
                for f in range(self._numFramesGrowth):
                    scotomasToChangeThisFrame = scotomaSequenceReverse[count:count+newScotomasPerFrameReverse[f]]
                    count += newScotomasPerFrameReverse[f]
                    mask[scotomasToChangeThisFrame] = addColor
                    scotomaMask.opacities = mask
                    grating.phase += self._numCyclesToShiftByFrame
                    grating.draw()
                    coverRectangle.draw()
                    scotomaMask.draw()
                    win.flip()
                    if self.checkQuitOrPause():
                        return
                    
            #bookend 2
            for f in range(self._numFramesBookend):
                grating.phase += self._numCyclesToShiftByFrame
                grating.draw()
                coverRectangle.draw()
                scotomaMask.draw()
                win.flip()
                if self.checkQuitOrPause():
                    return

            #tail time
            for f in range(self._tailTimeNumFrames):
                grating.draw()
                coverRectangle.draw()
                scotomaMask.draw()
                win.flip()
                if self.checkQuitOrPause():
                    return


            self._stimulusEndLog.append(trialClock.getTime())
            self.sendTTL()
            win.flip();win.flip() #two flips to allow for a pause for TTL writing

            self._numberOfEpochsCompleted += 1
            
        
        self._completed = 1
