#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import mysql.connector
from datetime import datetime, timedelta

__author__ = 'Nico Curti'
__email__ = 'nico.curti2@unibo.it'
__package__ = 'Filo Blu Read Messages Query'

# global variables that must be set and used in the following class
# The paths are relative to the current python file
CONFIGFILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'config.json'))

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

  cursor.execute('SELECT id_paziente, testo, scritto_il FROM messaggi WHERE scritto_il < "{0}" AND sa_score = 0'.format(now))

  result_query = cursor.fetchall()

  if result_query:

    patient_msg, text_msg, time_msg = zip(*result_query)

    # looking for biological parameters
    #two_days_ago  = now - timedelta(days=DT_BIOLOGICAL_SEARCH)
    cursor.execute('SELECT id_paziente, id_parametro_rilevato, valore FROM parametri_rilevati') # insert time filter
    patient_bio, patient_param, patient_bioval = zip(*cursor.fetchall())

    data_to_process = [None] * len(patient_msg)

    for i, patient in enumerate(patient_msg):
      for j, bio_patient in enumerate(patient_bio):
        if patient == bio_patient:
          data_to_process[i] = (text_msg[i], patient_msg[i], patient_param[j], patient_bioval[j], time_msg[i])
        else:
          data_to_process[i] = (text_msg[i], patient_msg[i], None,             None,              time_msg[i])

    print(data_to_process)

