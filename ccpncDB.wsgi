#!/usr/bin/env python

import sys
import os

sys.path.append( os.path.abspath(os.path.dirname(__file__)) )
sys.path.append( "/opt/rh/python27/root/usr/lib/python2.7/site-packages" )
sys.path.append( "/opt/rh/python27/root/usr/lib64/python2.7/site-packages" )

from main import app as application
