#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import time
import string
import threading
import unicodedata
import numpy as np
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
    - interval_seconds : (float) - clock time in seconds unit for the function repetition.
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

def read_dictionary(dict_file):
  """
  Read dictionary of words from file.
  The dictionary file must be sorted by frequency of words in ascending order.
  The file must be formatted as:

  word1 freq1
  word2 freq2

  with space as separator
  """
  words = {}
  with open(dict_file, 'r', encoding='utf-8') as fp:
    for line in fp:
      w, i = line.split(' ')
      words[w] = int(i)
  return words

def preprocess(msg, dictionary):
  """
  Pipeline for text pre-processing.
  The text message is converted in lower case and the punctuations are removed.
  The accents letters are replaced by the "normal" form (ex. à -> a) and the text is splitted in single words.
  The words are replaced by their frequency stored in the dictionary; the words outside the dictionary
  have 0 frequency.

  -------------

  Variables
    msg: string - the text message to pre-process
    dictionary: dict - dictionary of frequency words in which keys are words and values are integer of the freq order

  Return
    outvect: np.array(type=int) - the position of each word in the dictionary
  """


  # convert to lower
  msg = msg.lower()
  # remove punctuation
  msg = re.sub('['+string.punctuation+']', ' ', msg)
  msg.replace('\t', ' ').replace('\n', ' ').replace('\\', ' ')

  # replace accents
  nfkd_form = unicodedata.normalize('NFKD', msg)
  msg = u''.join([c for c in nfkd_form if not unicodedata.combining(c)])

  # split in words
  words = [i for i in msg.split(' ') if i != '']

  converted = []
  for word in words:
    if word in dictionary:
      tmp_idx = dictionary[word]
    elif word[:-1] in dictionary:
      tmp_idx = dictionary[word[:-1]]
    else:
      tmp_idx = 0

    converted.append(tmp_idx)

  outvect = np.asarray(converted).astype('i4')
  return outvect


def vectorize_sequence(seq, dim):
  """
  Convert matrix of words pre-processed by the preprocess function in a matrix of one-hot encoding of the dictionary

  -----------

  Variables
    seq: np.array(ndim=2, dtype=int) - matrix of the full set of messages pre-processed
    dim: int - dimension of the dictionary file

  Return
    results: np.array(ndim=2, dtype=float) - one-hot encoding of the messages
  """

  results = np.zeros(shape=(len(seq), dim), dtype=float)
  for i, s in enumerate(seq):
    results[i, s] = 1.
  return results
