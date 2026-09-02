#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 14 17:41:01 2025

@author: eeprotocol(:K2)
"""

class config:
    def __init__(self):
        # Arduino
        self.ARDUINO_PORT="COM7"
        
        # Thermo plate
        self.THERMO_PLATE=False
<<<<<<< Updated upstream
        self.THERMO_PLATE_PORT="COM8"
=======
        self.THERMO_PLATE_PORT="COM6"
>>>>>>> Stashed changes
        
        # Flow sensor
        self.FLOW_SENSOR=True
        
        # Selector valve
        self.SELECT_VALVE=True
        self.SELECT_VALVE_PORT="COM6"
        
        # Pressure regulator type (you can also change it in GUI)
        # 0=ITV0010
        # 1=ITV0030
        # 2=ITV0090
        # 3=EVL1050
        self.REG_TYPE=0
        
        
        
        
        
        