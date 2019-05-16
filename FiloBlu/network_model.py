#!/usr/bin/env python

from __future__ import division, print_function

import tensorflow as tf
import keras.backend as K
from keras.models import Model
from keras.layers import Input, Dense, Activation

from misc import preprocess, vectorize_sequence

__author__ = ['Andrea Ciardiello', 'Stefano Giagu', 'Nico Curti']
__email__ = ['andrea.ciardiello@gmail.com', 'stefano.giagu@roma1.infn.it', 'nico.curti2@unibo.it']
__package__ = 'Filo Blu Neural Network Model'

class NetworkModel(object):

  # batch size (number of traingin events after each weight update)
  BATCH_SIZE = 512

  MAX_WORDS = 12000 # max number of words

  def __init__ (self, weights_filename):

    self.net = self._load_model(weights_filename)


  def _load_model(self, weights_filename):

    nnet = self._model()
    nnet.load_weights(weights_filename)
    return nnet

  def _model(self):
    """
    NNet Architecture
    """

    # sequential (aka Feed-Forward Convolutional Neural Network) (functional approach)
    Input_txt = Input(shape=(self.MAX_WORDS,), name='input_txt')

    # dense_1
    x = Dense(16, input_shape=(self.MAX_WORDS,), name='dense_1')(Input_txt)
    x = Activation('relu', name='activation_1')(x)

    # dense_2
    x = Dense(8, name='dense_2')(x)
    x = Activation('relu', name='activation_2')(x)

    # dense_3 (output layer)
    x = Dense(1, name='dense_3')(x)
    out = Activation('sigmoid', name='activation_3')(x)

    # model:
    nnet = Model(inputs=[Input_txt], outputs=out)

    return nnet

  @property
  def summary(self):
    return self.net.summary



  def predict(self, text_list, dictionary):
    # pre-process data
    msgs = [preprocess(line, dictionary) for line in text_list]

    # Uncomment these lines if you are using a different dictionary
    #msgs = np.asarray(msgs)
    #msgs = [ [w for w in x if w <= MAX_WORDS] for x in msgs ]

    data = vectorize_sequence(msgs, dim=len(dictionary))

    # predict the whole list
    y_pred = self.net.predict(data, batch_size=self.BATCH_SIZE)
    return y_pred.ravel().tolist()


if __name__ == '__main__':

  import os
  from misc import read_dictionary

  weightfile = os.path.join(os.path.dirname(__file__), '..', 'data', 'SAna_DNN_trained_0_weights.h5')
  dictionary_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'DB_parole_filter.dat')

  nnet = NetworkModel(weightfile)
  print(nnet.summary())

  ilist = ['buongiorno dottore oggi ho la febbre alta e un fortissimo dolore al rene da una settimana',
           'ciao e tanti auguri di buon natale a lei e famiglia']

  dictionary = read_dictionary(dictionary_file)


  y_pred = nnet.predict(ilist, dictionary)

  print(y_pred)

