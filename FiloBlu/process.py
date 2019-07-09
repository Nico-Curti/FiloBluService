#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time

__author__ = 'Nico Curti'
__email__ = 'nico.curti2@unibo.it'
__package__ = 'Filo Blu Process service'

# global variables that must be set and used in the following class
# The paths are relative to the current python file
DICTIONARY = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'DB_parole_filter.dat'))
MODEL = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'SAna_DNN_trained_0_weights.h5'))
CONFIGFILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'config.json'))
LOGFILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs', 'filo_blu_process_service.log'))
UPDATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'updates'))


def parse_args():
  """
  Just a simple parser of the command line.
  There are not required parameters because the scripts can run also with the
  set of default variables set at the beginning of this script.

  -----

  Return

    args : object - Each member of the object identify a different command line argument (properly casted)
  """

  import argparse


  description = "Filo Blu Process Service"

  parser = argparse.ArgumentParser(description = description)
  parser.add_argument('--config',
                      dest='config',
                      type=str,
                      required=False,
                      action='store',
                      help='Json configuration file for DB credentials',
                      default=CONFIGFILE
                      )
  parser.add_argument('--logs',
                      dest='logs',
                      type=str,
                      required=False,
                      action='store',
                      help='Log filename with absolute path',
                      default=LOGFILE
                      )
  parser.add_argument('--network_model',
                      dest='model',
                      type=str,
                      required=False,
                      action='store',
                      help='Network Model weights filename',
                      default=MODEL
                      )
  parser.add_argument('--dictionary',
                      dest='dictionary',
                      type=str,
                      required=False,
                      action='store',
                      help='Word dictionary sorted by frequency',
                      default=DICTIONARY
                      )
  parser.add_argument('--update_dir',
                      dest='update_dir',
                      type=str,
                      required=False,
                      action='store',
                      help='Directory in which update models are stored',
                      default=UPDATE_DIR
                      )

  args = parser.parse_args()
  args.config = os.path.abspath(args.config)
  args.logs = os.path.abspath(args.logs)
  args.model = os.path.abspath(args.model)
  args.dictionary = os.path.abspath(args.dictionary)
  args.update_dir = os.path.abspath(args.update_dir)

  # Create the logs directory if it does not exist.
  log_directory = os.path.dirname(LOGFILE)
  os.makedirs(log_directory, exist_ok=True)
  os.makedirs(args.update_dir, exist_ok=True)

  return args



if __name__ == '__main__':

  """
  This main represent the tensorflow process service called by 'filoblu_service_tf.py' and it
  perform the right sequence of calls that can be found also in the 'filoblu_service_np.py' script
  in the main loop of the service object.
  """

  args = parse_args()

  from database import FiloBluDB

  db = FiloBluDB(args.config, args.logs)

  db.get_logger.info('LOADING PROCESSING MODEL...')

  try:

    from network_model_tf import NetworkModel

    net = NetworkModel(args.model)
    db.get_logger.info('MODEL LOADED')

  except Exception as e:

    db.log_error(e)

  db.get_logger.info('LOADING WORD DICTIONARY...')

  try:

    from misc import read_dictionary

    dictionary = read_dictionary(args.dictionary)
    db.get_logger.info('DICTIONARY LOADED')

  except Exception as e:

    db.log_error(e)


  db.callback_read_last_messages()
  time.sleep(10)
  db.callback_process_messages(net, dictionary)
  time.sleep(10)
  db.callback_write_score_messages()

  db.callback_load_new_weights(args.model, args.update_dir)
  db.callback_clear_log()
  db.callback_score_history_log(args.update_dir)

  db.get_logger.info('FILO BLU Service: STARTING UP')


  while True:

    if db._wait:
      net = NetworkModel(args.model)
      db._wait = False

  db.log_error('FILO BLU Service: SHUTDOWN')


