#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import division

import os
import sys
import time
import getpass
import requests
from zipfile import ZipFile

__author__  = 'Nico Curti'
__email__ = 'nico.curti2@unibo.it'

def download_file_from_google_drive(Id, destination, total_length=1505781):

  url = 'https://docs.google.com/uc?export=download'

  def get_confirm_token(response):
    for key, value in response.cookies.items():
      if key.startswith('download_warning'): return value
    return None

  def save_response_content(response, destination):
    chunk_size = 32768
    with open(destination, 'wb') as fp:
      dl = 0
      start = time.time()
      download = time.time()
      for chunk in response.iter_content(chunk_size):
        dl += len(chunk)
        done = int(50 * dl / total_length)
        download = time.time()
        if chunk: # filter out keep-alive new chunks
          fp.write(chunk)

  session  = requests.Session()
  response = session.get(url, params = {'id' : Id }, stream = True)
  token    = get_confirm_token(response)

  if token:
    params = { 'id' : Id, 'confirm' : token }
    response = session.get(url, params = params, stream = True)

  save_response_content(response, destination)


def get_weights(Id):

  size = 1505781
  file = 'filoblu_data'
  print ('Download {0} file...'.format(file))
  download_file_from_google_drive(Id, './{}.zip'.format(file.lower()), size)

  here = os.path.join(os.path.dirname(__file__))

  pwd = getpass.getpass('Password:')

  print ('Extracting files...', end='')

  try:
    with ZipFile('./{}.zip'.format(file.lower())) as zipper:
      zipper.extractall('.', pwd=pwd.encode())
    print ('[done]')
  except:
    print ('\n')
    print ('Wrong Password given! Ask to the authors for the right password')
    exit (1)

  try:
    os.makedirs(os.path.join(here, '../data'), exist_ok=True)
  except:
    os.makedirs(os.path.join(here, '../data'))

  os.rename('./dual_w_0_2_class_ind_cw.h5'.format(file.lower()), os.path.join(here, '../data/dual_w_0_2_class_ind_cw.h5'.format(file.lower())) )
  os.rename('./dual_w_0_2_class_ind_cw.pkl'.format(file.lower()), os.path.join(here, '../data/dual_w_0_2_class_ind_cw.pkl'.format(file.lower())) )
  os.rename('./updated_dictionary.dat'.format(file.lower()), os.path.join(here, '../data/updated_dictionary.dat'.format(file.lower())) )

  os.remove('./{}.zip'.format(file.lower()))


if __name__ == '__main__':

  get_weights('1BS4NgdvyTKDsVRgeVbzMOKm6hJG5u9u')
