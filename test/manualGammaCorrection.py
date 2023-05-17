#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 12 16:59:13 2022

@author: piccolo
"""
from psychopy import core, visual, data, event, monitors

w = visual.Window(
    monitor = 'projector_405',
    screen = 1,
    fullscr = True,
    color = -1,
    )


w.color = 1;
w.flip()

import numpy as np
luminanceVals = np.linspace(-1, 1, 11)
records = []
for v in luminanceVals:
    w.color = v
    w.flip()
    w.flip()
    records.append(float(input('Enter Value to move on: ')))

w.close()

adjustedLuminance = np.linspace(0, 1, 11)
g = monitors.GammaCalculator(adjustedLuminance, records, eq=1)
m = monitors.Monitor('projector_405')
m.setGamma(g.gamma)
m.save()
