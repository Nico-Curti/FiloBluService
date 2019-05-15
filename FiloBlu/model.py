#!/usr/bin/env python

from __future__ import division, print_function

import tensorflow as tf
import keras.backend as K
from keras.models import Model
from keras.optimizers import RMSprop
from keras.layers import Input, Dense, Activation

__author__ = ['Andrea Ciardiello', 'Stefano Giagu', 'Nico Curti']
__email__ = ['andrea.ciardiello@gmail.com', 'stefano.giagu@roma1.infn.it', 'nico.curti2@unibo.it']
__package__ = 'Filo Blu Neural Network Model'

# set memory usage 'on demand'
tf_config = tf.ConfigProto()
K.tensorflow_backend.set_session(tf.Session(config=tf_config))

# learning rate decay parameters (if LR_ST=LR_END not used)
LR_ST = 1e-3
# batch size (number of traingin events after each weight update)
BATCH_SIZE = 512

MAX_WORDS = 12000 # max number of words



def model():
  """
  NNet Architecture
  """

  # sequential (aka Feed-Forward Convolutional Neural Network) (functional approach)
  Input_txt = Input(shape=(MAX_WORDS,), name='input_txt')

  # dense_1
  x = Dense(16, input_shape=(MAX_WORDS,), name='dense_1')(Input_txt)
  x = Activation('relu', name='activation_1')(x)

  # dense_2
  x = Dense(8, name='dense_2')(x)
  x = Activation('relu', name='activation_2')(x)

  # dense_3 (output layer)
  x = Dense(1, name='dense_3')(x)
  out = Activation('sigmoid', name='activation_3')(x)

  # model:
  nnet = Model(inputs=[Input_txt], outputs=out)

  # Model Compile

  optimizer = RMSprop(lr=LR_ST)

  nnet.compile(optimizer=optimizer, loss='binary_crossentropy', metrics=['accuracy'])

  return nnet


if __name__ == '__main__':

  import os

  weightfile = os.path.join(os.path.dirname(__file__), '..', 'data', 'SAna_DNN_trained_0_weights.h5')

  nnet = model()
  nnet.summary()
  nnet.load_weights(weightfile)
