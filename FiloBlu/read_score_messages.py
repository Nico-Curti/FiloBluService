#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import mysql.connector
from datetime import datetime, timedelta

__author__ = 'Nico Curti'
__email__ = 'nico.curti2@unibo.it'

# global variables that must be set and used in the following class
# The paths are relative to the current python file
CONFIGFILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'config.json'))
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


  description = "Filo Blu Process Read Query"

  parser = argparse.ArgumentParser(description = description)
  parser.add_argument('--config',
                      dest='config',
                      type=str,
                      required=False,
                      action='store',
                      help='Json configuration file for DB credentials',
                      default=CONFIGFILE
                      )


  args = parser.parse_args()
  args.config = os.path.abspath(args.config)

  # Create the logs directory if it does not exist.

  return args

if __name__ == '__main__':

  """
  This main read messages from db with a custom query.
  """

  args = parse_args()

  with open(args.config, 'r', encoding='utf-8') as fp:
    config = json.load(fp)

  db = mysql.connector.connect(
                              host = config['host'],
                              user = config['username'],
                              passwd = config['password'],
                              database = config['database']
                              )
  cursor = db.cursor()

  now = datetime.now()

  cursor.execute('SELECT testo, sa_score, sa_valutazione, sa_medico FROM messaggi WHERE scritto_il < "{0}"'.format(now))

  history_score_filename = os.path.join(UPDATE_DIR, 'FiloBlu_Score_History.csv')

  with open(history_score_filename, 'w', encoding='utf-8') as fp:
    fp.write('text_message,nn_predict_score,validation_score,doctor_id\n')
    for txt, sa_score, sa_val, sa_doc in cursor.fetchall():
      txt = txt.replace('\n', '').replace('\r', '')
      fp.write(','.join(['"' + txt + '"', str(sa_score), str(sa_val), str(sa_doc)]) + '\n')
