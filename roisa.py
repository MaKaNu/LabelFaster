#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ctypes
import sys

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from models import image_loader, ROI_controller, KeyMonitor
from views import StartWindow, startApp

from libs.utils import *
from libs.resources import *

if __name__ == '__main__':
    sys.exit(startApp())
