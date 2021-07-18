# -*- coding: utf-8 -*-
"""
Created on Mon Jul 12 16:17:29 2021



@author: mrsco
"""
from protocols.protocol import protocol

class MovingGratingDirection(protocol):
    def __init__(self):
        super().__init__()
        self.protocolName = 'MovingGratingDirection'
    
    def estimateTime(self):
        return 0