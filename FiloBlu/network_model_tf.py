#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf
tf.logging.set_verbosity(tf.logging.ERROR)

from keras.models import Model
from keras.layers import Input, Dense, Activation
import numpy as np

from misc import preprocess, vectorize_sequence

global DEFAULT_GRAPH
DEFAULT_GRAPH = tf.get_default_graph()

__author__ = ['Andrea Ciardiello', 'Stefano Giagu', 'Nico Curti']
__email__ = ['andrea.ciardiello@gmail.com', 'stefano.giagu@roma1.infn.it', 'nico.curti2@unibo.it']

class NetworkModel(object):

  # batch size (number of training events after each weight update)
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

    Input_txt = Input(shape=(self.MAX_WORDS,), name='input_txt')

    # dense_1
    x = Dense(16, input_shape=(self.MAX_WORDS,), name='dense_1')(Input_txt)
    x = Activation('relu', name='activation_1')(x)

    # dense_2
    x = Dense(8, name='dense_2')(x)
    x = Activation('relu', name='activation_2')(x)

    # dual output
    # dense_3 (output layer)
    out_type = Dense(3, name='out_type')(x)
    out_type = Activation('softmax', name='activation_type')(out_type)
    
    # dense_3 (output layer)
    out_P = Dense(4, name='out_P')(x)
    out_P = Activation('softmax', name='activation_P')(out_P)    
   
    nnet = Model(inputs=[Input_txt], outputs=[out_type,out_P])

    return nnet

  @property
  def summary(self):
    return self.net.summary



  def predict(self, text_list, bio_params, dictionary, binning):

    # pre-process data
    msgs = [preprocess(line, dictionary) for line in text_list]

    # Uncomment these lines if you are using a different dictionary
    # msgs = np.asarray(msgs)
    # msgs = [ [w for w in x if w <= MAX_WORDS] for x in msgs ]

    text_data = vectorize_sequence(msgs, dim=len(dictionary))

    # predict the whole list + biological parameters
    with DEFAULT_GRAPH.as_default():

      dual_pred = self.net.predict(text_data, batch_size=self.BATCH_SIZE)
      #dual out - divided to be compatible with last version
      #y_type is topics prediction. y_pred is priority prediction as last version
      type_pred = dual_pred[0] # topics prediction, not used
      y_pred = dual_pred[1] # priority prediction - 4 float as probability for each attention level
      y_pred=np.argmax(y_pred,axis=1)+1  # class assignment 1 -less attention
                                                          # 4 - most attention
      
    #

   # if binning: #not required anymore. Now there are 4 indipendent classes
      #bins = [0., .25, .5, .75, 1.]
      
      #y_pred = np.digitize(y_pred, bins)
    

      return list(map(int, y_pred))

    


if __name__ == '__main__':

  import os
  from misc import read_dictionary

  #weightfile = os.path.join(os.path.dirname(__file__), '..', 'data', 'SAna_DNN_trained_0_weights.h5')
  # NEW architeture
  weightfile = os.path.join(os.path.dirname(__file__), '..', 'data', 'dual_w_0_2_class_ind_cw.h5')
  dictionary_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'DB_parole_filter.dat')

  nnet = NetworkModel(weightfile)
  print(nnet.summary())

  ilist = [
           ['buongiorno dottore oggi ho la febbre alta e un fortissimo dolore al rene da una settimana',
           'ciao e tanti auguri di buon natale a lei e famiglia'],
           None, None, None
           ]

  dictionary = read_dictionary(dictionary_file)


  y_pred = nnet.predict(ilist, dictionary)

  print(y_pred)

