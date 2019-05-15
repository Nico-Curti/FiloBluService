#!/usr/bin/env python

from __future__ import division, print_function

import re
import time
import string
import unicodedata
import numpy as np

from model import model, MAX_WORDS, BATCH_SIZE

__author__ = ['Andrea Ciardiello', 'Stefano Giagu', 'Nico Curti']
__email__ = ['andrea.ciardiello@gmail.com', 'stefano.giagu@roma1.infn.it', 'nico.curti2@unibo.it']
__package__ = 'Filo Blu Text Message prediction'

def load_model(weightfile):

  nnet = model()
  nnet.load_weights(weightfile)

  return nnet

def read_dictionary(dict_file):
  words = {}
  with open(dict_file, 'r', encoding='utf-8') as fp:
    for line in fp:
      w, i = line.split(' ')
      words[w] = int(i)
  return words

def preprocess(msg, dictionary):

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
      tmp_idx = dictionary[word]
    else:
      tmp_idx = 0

    converted.append(tmp_idx)

  outvect = np.asarray(converted).astype('i4')
  return outvect


def vectorize_sequence(seq, dim = 10000):
  results = np.zeros(shape=(len(seq), dim))
  for i, s in enumerate(seq):
    results[i, s] = 1
  return results

def predict(net, text_list, dictionary):

  # pre-process data
  msgs = [preprocess(line, dictionary) for line in text_list]

  # Uncomment these lines if you are using a different dictionary
  #msgs = np.asarray(msgs)
  #msgs = [ [w for w in x if w <= MAX_WORDS] for x in msgs ]

  data = vectorize_sequence(msgs, dim=len(dictionary))

  # predict the whole list
  y_pred = net.predict(data, batch_size=BATCH_SIZE)
  return y_pred


if __name__ == '__main__':

  import os

  weightfile = os.path.join(os.path.dirname(__file__), '..', 'data', 'SAna_DNN_trained_0_weights.h5')
  dictionary_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'DB_parole_filter.dat')

  nnet = load_model(weightfile)

  ilist=['buongiorno dottore oggi ho la febbre alta e un fortissimo dolore al rene da una settimana',
         'ciao e tanti auguri di buon natale a lei e famiglia']

  dictionary = read_dictionary(dictionary_file)


  y_pred = predict(nnet, ilist, dictionary)

  print(y_pred)
