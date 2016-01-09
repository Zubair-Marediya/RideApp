#!/usr/bin/env python

import os
import readline
from pprint import pprint

from flask import *

from server.py import *
from utils import *
from db import *
from models import *


os.environ['PYTHONINSPECT'] = 'True'