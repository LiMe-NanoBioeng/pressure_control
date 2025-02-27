# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 16:37:45 2019

@author: shintaku
"""

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure 
from matplotlib import rcParams

# Setting the layout of figure
rcParams['font.size'] = 9


class MatplotlibWidget(Canvas):
    def __init__(self, parent=None, title='', xlabel='', ylabel='',
                 xlim=None, ylim=None, xscale='linear', yscale='linear',
                 width=4, height=3, dpi=200):
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        # self.axes = self.figure.add_subplot(121)
        # self.axes.set_title(title)
        # self.axes.set_xlabel(xlabel)
        # self.axes.set_ylabel(ylabel)
        # if xscale is not None:
        #     self.axes.set_xscale(xscale)
        # if yscale is not None:
        #     self.axes.set_yscale(yscale)
        # if xlim is not None:
        #     self.axes.set_xlim(*xlim)
        # if ylim is not None:
        #     self.axes.set_ylim(*ylim)
        # Add 3 subplots in a 1 row x 3 columns layout
        self.axes1 = self.figure.add_subplot(131)  # First plot (1st column)
        self.axes2 = self.figure.add_subplot(132)  # Second plot (2nd column)
        self.axes3 = self.figure.add_subplot(133)  # Third plot (3rd column)
        
        # Set titles, labels, and other properties for each subplot
        self.axes1.set_title(title)
        self.axes1.set_xlabel(xlabel)
        self.axes1.set_ylabel(ylabel)
        
        self.axes2.set_title(title)
        self.axes2.set_xlabel(xlabel)
        self.axes2.set_ylabel(ylabel)
        
        self.axes3.set_title(title)
        self.axes3.set_xlabel(xlabel)
        self.axes3.set_ylabel(ylabel)
        
        # Set scales and limits for each subplot if provided
        if xscale is not None:
            self.axes1.set_xscale(xscale)
            self.axes2.set_xscale(xscale)
            self.axes3.set_xscale(xscale)
        if yscale is not None:
            self.axes1.set_yscale(yscale)
            self.axes2.set_yscale(yscale)
            self.axes3.set_yscale(yscale)
        if xlim is not None:
            self.axes1.set_xlim(*xlim)
            self.axes2.set_xlim(*xlim)
            self.axes3.set_xlim(*xlim)
        if ylim is not None:
            self.axes1.set_ylim(*ylim)
            self.axes2.set_ylim(*ylim)
            self.axes3.set_ylim(*ylim)

        super(MatplotlibWidget, self).__init__(self.figure)
        self.setParent(parent)
        super(MatplotlibWidget, self).setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        super(MatplotlibWidget, self).updateGeometry()

    def sizeHint(self):
        return QSize(*self.get_width_height())

    def minimumSizeHint(self):
        return QSize(10, 10)