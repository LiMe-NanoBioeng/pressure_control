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
        def acquire_image(json_load):
            # core = Core()
            num_time_points = json_load.get("numFrames")
            time_interval_s = json_load.get("intervalMs")
            z_start = json_load.get("sliceZTopUm", 0)
            z_end = json_load.get("sliceZBottomUm", 0)
            z_step  = json_load.get("sliceZStepUm", 1)
            channels_info = json_load.get("channels", [])
            channel_group = json_load.get("channelGroup", None)
            channels = [ch["config"] for ch in channels_info if ch.get("useChannel", False)]
            
            with Acquisition(directory='.', name='acquisition_name') as acq:
                events = multi_d_acquisition_events(
                    num_time_points = num_time_points,
                    time_interval_s = time_interval_s,
                    channel_group = channel_group,
                    channels = channels,
                    z_start = z_start, 
                    z_end = z_end,
                    z_step = z_step,
                    order='tzc')
                acq.acquire(events)

            # with Acquisition(directory='.', name='acquisition_name') as acq:
            #     events = multi_d_acquisition_events(
            #         num_time_points=4, time_interval_s=0,
            #         channel_group='Exposure', channels=['4_Red', '3_Green','2_Blue'],
            #         z_start=0, z_end=6, z_step=0.4,
            #         order='tzc')
            #     acq.acquire(events)
                
        def load_acq_setting():
            json_open = open('C://Users//lab//Documents//AcqSettings.txt','r')
            json_load = json.load(json_open)
            return(json_load)
        

from pycromanager import MagellanAcquisition

# no need to use the normal "with" syntax because these acquisition are cleaned up automatically
acq = MagellanAcquisition(magellan_acq_index=0)
acq.await_completion()

# Or do this to launch an explore acquisition
#acq = MagellanAcquisition(magellan_explore=True)











        



            
   
          
        




        