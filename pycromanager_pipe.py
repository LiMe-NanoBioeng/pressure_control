# -*- coding: utf-8 -*-
"""
Created on Sun Aug 24 10:32:41 2025

@author: lab
"""
import os
import numpy as np
import pytest
import time
import json
from pycromanager import Acquisition, Core, multi_d_acquisition_events
from pycromanager.acquisition.acquisition_superclass import AcqAlreadyCompleteException
import matplotlib.pyplot as plt
from pycromanager import  test
class acq_pycromanager():
        def __init__(self,mda_file=None,pos_file=None):
            self.MDA_file_path = mda_file
            self.Pos_file_path = pos_file
    
        def load_acq_setting(self):
             #json_open = open('C://Users//lab//Desktop//AcqSettings_4.txt','r')
             json_open = open(self.MDA_file_path,'r')
             json_load = json.load(json_open)
             return(json_load)
        
        def load_positions_from_pos(self):
            #filepath = 'C://Users//lab//Documents//test..pos'
            filepath = self.Pos_file_path
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            positions = data["map"]["StagePositions"]["array"]
            coords = []
            for pos in positions:
                devices = pos["DevicePositions"]["array"]
                x = y = None
                for dev in devices:
                    name = dev["Device"]["scalar"]
                    values = dev["Position_um"]["array"]
                    if name == "TIXYDrive":
                        x, y = values
                coords.append((x, y))
            return coords    
    
        def acquire_image(self):
            json_load = self.load_acq_setting()
            coords = self.load_positions_from_pos()
            
            num_time_points = json_load.get("numFrames")
            time_interval_s = json_load.get("intervalMs")
            z_start = json_load.get("sliceZBottomUm", 0)
            z_end = json_load.get("sliceZTopUm", 0)
            if z_start > z_end:
             z_start, z_end = z_end, z_start
            z_step  = json_load.get("sliceZStepUm", 1)
            channels_info = json_load.get("channels", [])
            channel_group = json_load.get("channelGroup", None)
            channels = [ch["config"] for ch in channels_info if ch.get("useChannel", False)]
            channel_exposures_ms = [ch["exposure"] for ch in channels_info if ch.get("useChannel", False)]
            xy_positions = np.array(coords)
            root = json_load.get("root",".")
            prefix = json_load.get("prefix")
            # save_mode = json_load.get("saveMode")
            print(channels)
            print(channel_exposures_ms)
            
            with Acquisition(directory=root, name=prefix) as acq:
                events = multi_d_acquisition_events(
                    num_time_points = num_time_points,
                    time_interval_s = time_interval_s,
                    channel_group = channel_group,
                    channels = channels,
                    channel_exposures_ms = channel_exposures_ms,
                    xy_positions = xy_positions,
                    z_start = z_start, 
                    z_end = z_end,
                    z_step = z_step,
                    order='tpcz')
                acq.acquire(events)
                   
if __name__ == "__main__":
    acq = acq_pycromanager()
    acq.acquire_image()
    print("done")
        

# from pycromanager import MagellanAcquisition

# # no need to use the normal "with" syntax because these acquisition are cleaned up automatically
# acq = MagellanAcquisition(magellan_acq_index=0)
# acq.await_completion()

# Or do this to launch an explore acquisition
#acq = MagellanAcquisition(magellan_explore=True)
