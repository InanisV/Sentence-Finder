import os
import sys
import math
import time
import queue
import pickle
import threading
from peewee import *
import PySimpleGUI as sg
from Txporn import Txporn
from textblob import TextBlob
from collections import Counter
from asyncio import set_event_loop, new_event_loop, get_event_loop, wait, ensure_future