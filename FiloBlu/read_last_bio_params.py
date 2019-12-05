#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import mysql.connector
from datetime import datetime
from collections import defaultdict

__author__ = 'Nico Curti'
__email__ = 'nico.curti2@unibo.it'

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
                              user = config['username'],
                              host = config['host'],
                              passwd = config['password'],
                              database = config['database']
                              )
  cursor = db.cursor()

  cursor.execute('SHOW columns FROM parametri_rilevati_gruppo')

  cols = [i for i in cursor]
  print(cols)

  now = datetime.now()

  cursor.execute('SELECT parametri_rilevati.id_paziente, parametri_rilevati.valore, parametri.nome \
                                AS nome_parametro, parametri_rilevati_gruppo.data AS nome_gruppo \
                                FROM parametri_rilevati JOIN parametri \
                                ON (parametri_rilevati.id_parametro = parametri.id_parametro) \
                                JOIN parametri_rilevati_gruppo \
                                ON (parametri_rilevati.id_parametro_rilevato_gruppo = parametri_rilevati_gruppo.id_parametro_rilevato_gruppo) \
                                JOIN parametri_gruppi ON (parametri_gruppi.id_gruppo_parametro = parametri_rilevati_gruppo.id_gruppo) \
                                WHERE parametri_rilevati_gruppo.data <= "{0}" '.format(now))

  result_query = defaultdict(dict)
  for patient_bio, patient_bioval, patient_param, bio_time in cursor.fetchall():
    result_query[patient_bio][patient_param] = patient_bioval

  print(json.dumps(result_query, indent = 4))

