#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 14 17:41:01 2025

@author: eeprotocol(:K2)
"""

class config:
    def __init__(self):
        #Arduino
        self.ARDUINO_PORT="/dev/ttyACM1"
        
        # Thermo plate
        self.THERMO_PLATE=False
        self.THERMO_PLATE_PORT="COM10"
        
        #Flow sensor
        self.FLOW_SENSOR=False
        
        #Selector valve
        self.SELECT_VALVE=False
        self.SELECT_VALVE_PORT="COM11"
        