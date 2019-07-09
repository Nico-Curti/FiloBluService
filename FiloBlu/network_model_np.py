#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function

import pickle
import numpy as np
from misc import preprocess, vectorize_sequence

__author__ = ['Andrea Ciardiello', 'Stefano Giagu', 'Nico Curti']
__email__ = ['andrea.ciardiello@gmail.com', 'stefano.giagu@roma1.infn.it', 'nico.curti2@unibo.it']
__package__ = 'Filo Blu Neural Network Model'


class Dense(object):

  def __init__(self, output_shape, input_shape, activation, name='', weights=None, biases=None):

    if weights is not None:

      self._weights = weights
      if self._weights.shape != (input_shape, output_shape):
        raise ValueError('Inconsistent size of the weights in layer {}'.format(name))

    else:

      scale = np.sqrt(2. / input_shape)
      self._weights = np.random.uniform(low=-1., high=1., size=(input_shape, output_shape)) * scale

    if biases is not None:

      self._bias = biases
      if self._bias.shape != (output_shape,):
        raise ValueError('Inconsistent size of the bias in layer {}'.format(name))

    else:

      self._bias = np.zeros(shape=(output_shape,))

    self._name = name

    if not callable(activation):
      raise Exception('Activation function must be a callable function or lambda')

    self._activation = activation

  def predict(self, input_array):
    return self._activation( ( input_array @ self._weights ) + self._bias )

  def load(self, params):
    self._weights, self._bias = params

  @property
  def outputs(self):
    return self._bias.size

  @property
  def size(self):
    return self._weights.size + self._bias.size

  @property
  def shape(self):
    return self._weights.shape

  @property
  def name(self):
    return '{} (Dense)'.format(self._name)


class Concatenate(object):

  def __init__(self, layers, axis=1):
    self.idx_layer_1, self.idx_layer_2 = layers
    self.axis = axis

  def predict(self, input_array):
    return np.concatenate()



class Input(object):

  def __init__(self, shape=tuple(), name=''):
    self._data = np.empty(shape=shape)
    self._name = name

  def predict(self, input_array=None):
    return input_array

  @property
  def outputs(self):
    return self._data.size

  @property
  def size(self):
    return self._data.size

  @property
  def shape(self):
    return self._data.shape

  @property
  def name(self):
    return '{} (Input)'.format(self._name)



class NetworkModel(object):

  MAX_WORDS = 12000 # max number of words
  BATCH_SIZE = 512 # max number of message to process at the same time

  def __init__(self, weights_filename=None):

    if weights_filename:
      model = self._load_weights(weights_filename)
    self.net = self._load_model(model=model)

  def _load_model(self, model=None):

    net = self._model(model)
    return net

  def _sigmoid(self, x, derivate=False):
    sigm = 1. / (1. + np.exp(-x))
    return sigm * (1. - sigm) if derivate else sigm

  def _relu(self, x):
    x[x < 0] = 0.
    return x

  def _load_weights(self, weights_filename):
    with open(weights_filename, 'rb') as fp:
      model = pickle.load(fp)

    return model

  def _model(self, model=None, seed=123):
    """
    NNet Architecture
    """
    np.random.seed(seed)

    if len(model) != 6:
      raise ValueError('The model loaded not correspond to the NNet architecture')

    net = []

    #net.append( Input(shape=(1, self.MAX_WORDS), name='input_txt') )

    # dense_1
    net.append( Dense(16, self.MAX_WORDS, self._relu, name='dense_1', weights=model[0], biases=model[1]) )

    # dense_2
    net.append( Dense(8, net[-1].outputs, self._relu, name='dense_2', weights=model[2], biases=model[3]) )

    # dense_3
    net.append( Dense(1, net[-1].outputs, self._sigmoid, name='dense_3', weights=model[4], biases=model[5]) )

    return net

  def summary(self):

    separator = '_________________________________________________________________'
    header = '\n'.join([ separator,
                         'Layer (type)                 Output Shape              Param #   ',
                         '=================================================================',
                         ''
                       ])

    body = '\n{}\n'.format(separator).join( [
                                           '{0:29}({1[0]:^5}, {1[1]:^5}){2:^30}'.format(layer.name, layer.shape, layer.size)
                                           for layer in self.net
                                            ] )

    total_params = np.sum([v.size for v in self.net if isinstance(v, np.ndarray)])

    tail = '\n'.join([
                      '=================================================================',
                      'Total params: {}'.format(int(total_params)),
                      'Trainable params: {}'.format(int(total_params)),
                      'Non-trainable params: 0',
                      separator,
                      ''
                    ])
    return '\n'.join([header, body, tail])


  def _predict(self, input_data):

    input_data = [np.expand_dims(i, axis=0) for i in input_data]
    score = np.empty(shape=(len(input_data), ))
    for i, data in enumerate(input_data):
      for layer in self.net:
        res = layer.predict(data)
        data = res
      score[i] = res

    return score


  def predict(self, text_list, bio_params, dictionary, binning=True):

    # pre-process data
    msgs = [preprocess(line, dictionary) for line in text_list]

    # Uncomment these lines if you are using a different dictionary
    #msgs = np.asarray(msgs)
    #msgs = [ [w for w in x if w <= MAX_WORDS] for x in msgs ]

    text_data = vectorize_sequence(msgs, dim=len(dictionary))

    # predict the whole list

    y_pred = self._predict(text_data) # miss biological parameter pre-processed

    # binning the value between [1, 4]

    if binning:
      bins = [0., .25, .5, .75, 1.]
      y_pred = np.digitize(y_pred, bins)

      return list(map(int, y_pred))

    else:

      return list(map(float, y_pred))


if __name__ == '__main__':

  import os
  from misc import read_dictionary

  weightfile = os.path.join(os.path.dirname(__file__), '..', 'data', 'SAna_DNN_trained_0_weights.pkl')
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

