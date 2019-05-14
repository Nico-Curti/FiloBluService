#!/usr/bin/env python

import time
import threading
from functools import wraps

__author__ = 'Nico Curtix'
__email__ = 'nico.curti2@unibo.it'
__package__ = 'Filo Blu miscellaneous'

# Source: https://medium.com/@mgarod/dynamically-add-a-method-to-a-class-in-python-c49204b85bd6
def add_method(cls):

  def decorator(func):

    @wraps(func)
    def wrapper(self, *args, **kwargs):
      return func(*args, **kwargs)

    setattr(cls, func.__name__, wrapper)
    # Note we are not binding func, but wrapper which accepts self but does exactly the same as func
    return func # returning func means func can still be used normally

  return decorator

def repeat_interval(interval_seconds):

  def decorator(function):

    @wraps(function)
    def wrapper(*args, **kwargs):
      stopped = threading.Event()

      def loop(): # executed in another thread
        while not stopped.wait(interval_seconds): # until stopped
          function(*args, **kwargs)

      t = threading.Thread(target=loop)
      t.daemon = True # stop if the program exits
      t.start()
      return stopped

    return wrapper

  return decorator

def repeat_precise_time(date):

  def decorator(function):

    @wraps(function)
    def wrapper(*args, **kwargs):
      stopped = threading.Event()

      def loop():
        while not stopped.wait_for(time.time() == date):
          function(*args, **kwargs)

      t = threading.Thread(target=loop)
      t.daemon = True # stop if the program exits
      t.start()
      return stopped

    return wrapper

  return decorator

