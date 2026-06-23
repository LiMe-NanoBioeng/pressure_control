# -*- coding: utf-8 -*-
"""
Created on Sun Aug 24 10:32:41 2025

@author: lab
"""
from pycromanager_pipe import acq_pycromanager
#mda_file = r"C:\Users\lab\20260608\AcqSettings.txt"
mda_file = r"C:\Users\lab\20260623\AcqSettings.txt"
pos_file = r"C:\Users\lab\Documents\Data\20260123_Test\20260203_Pycro_test\PositionList.pos"
#pos_file = r"C:\Users\lab\Documents\Data\20260608_test\PositionList.pos"
print(mda_file,pos_file)
acq = acq_pycromanager(mda_file,pos_file)
print("before acquire")
acq = acq.acquire_image()
print('sucess_acquirment')