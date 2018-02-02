#!/usr/bin/env python

import sys
import os
import json

current_path = os.path.abspath(os.path.dirname(__file__))

sys.path.append( current_path )

try:
    config = json.load(open( os.path.join(current_path,"config","config.json"), "r"))
except:
    config = {}

try:
    for p in config["pythonpath"]:
        sys.path.append(p)

except:
    pass

from main import app as application
