#!/usr/bin/env python

from __future__ import print_function, division

import os
import sys
import time
import getpass
import requests
from zipfile import ZipFile

__package__ = "Download Neural Network weights file"
__author__  = 'Nico Curti (nico.curti2@unibo.it)'

def download_file_from_google_drive(Id, destination, total_length = ): ###TODO

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
        sys.stdout.write('\r[%s%s] %3d%% (%1.1f Mb/sec) %3.0f sec' % ('=' * done,
                                                                   ' ' * (50 - done),
                                                                   dl / total_length * 100,
                                                                   len(chunk) / 1000000 / (time.time() - download),
                                                                   time.time() - start)
                                                                  )
        download = time.time()
        sys.stdout.flush()
        if chunk: # filter out keep-alive new chunks
          fp.write(chunk)
    sys.stdout.write('\n')

  session  = requests.Session()
  response = session.get(url, params = {'id' : Id }, stream = True)
  token    = get_confirm_token(response)

  if token:
    params = { 'id' : Id, 'confirm' : token }
    response = session.get(url, params = params, stream = True)

  save_response_content(response, destination)


def get_weights(Id):

  size = 0 ### TODO
  file = '' ### TODO
  print ('Download {0} file...'.format(file))
  download_file_from_google_drive(Id, './{}.zip'.format(file.lower()), size)

  here = os.path.join(os.path.dirname(__file__))

  pwd = getpass.getpass('Password:')

  print ('Extracting files...', end='')

  try:
    with ZipFile('./{}.zip'.format(file.lower())) as zipper:
      zipper.extractall('.', pwd=pwd)
    print ('[done]')
  except:
    print ('\n')
    print ('Wrong Password given! Ask to the authors for the right password')
    exit (1)

  try:
    os.makedirs(os.path.join(here, '../data'), exist_ok=True)
  except:
    os.makedirs(os.path.join(here, '../data'))

  os.rename('./{}.pth'.format(file.lower()), os.path.join(here, '../data/{}.pth'.format(file.lower())) )

  os.remove('./{}.zip'.format(file.lower()))


if __name__ == '__main__':

  get_weights('') ### TODO
