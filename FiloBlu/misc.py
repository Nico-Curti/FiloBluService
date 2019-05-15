#!/usr/bin/env python

import time
import threading
from functools import wraps

__package__ = 'Filo Blu miscellaneous'
__author__ = 'Nico Curti'
__email__ = 'nico.curti2@unibo.it'

# Source: https://medium.com/@mgarod/dynamically-add-a-method-to-a-class-in-python-c49204b85bd6
def add_method(cls):
  """
  This function create a very useful decorator to add an external and "new" function
  to an existing class type (cls variable).

  --------

  Variable
    - cls : (type) - class type in which the decorated function must be added.
  """

  def decorator(func):

    @wraps(func)
    def wrapper(self, *args, **kwargs):
      return func(*args, **kwargs)

    setattr(cls, func.__name__, wrapper)
    # Note we are not binding func, but wrapper which accepts self but does exactly the same as func
    return func # returning func means func can still be used normally

  return decorator

def repeat_interval(interval_seconds):
  """
  This function create a very useful decorator to asynchronously run the decorated function at each
  interval time given as parameter.

  ---------

  Variable
    - interval_seconds : (int) - clock time in seconds unit for the function repetition.
  """

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


