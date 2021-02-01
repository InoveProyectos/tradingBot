#!/usr/bin/env python

__author__ = "Inove Coding School"
__email__ = "INFO@INOVE.COM.AR"
__version__ = "1.0"

# Debug
print('__file__={0:<35} | __name__={1:<25} | __package__={2:<25}'.format(__file__,__name__,str(__package__)))

from flask import Flask

app = Flask(__name__)

#from handlers import monitor
from . import handlers