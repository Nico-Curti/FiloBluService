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
DICTIONARY = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'DB_parole_filter.dat'))
MODEL = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'SAna_DNN_trained_0_weights.pkl'))

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

  # Load Dictionary

  from misc import read_dictionary

  dictionary = read_dictionary(args.dictionary)

  # Load NN model

  from network_model_np import NetworkModel

  net = NetworkModel(args.model)

  db = mysql.connector.connect(
                              host = config['host'],
                              user = config['username'],
                              passwd = config['password'],
                              database = config['database']
                              )
  cursor = db.cursor()

  now = datetime.now()

  cursor.execute('SELECT id_paziente, testo, scritto_il FROM messaggi WHERE scritto_il < "{0}"'.format(now))

  result_query = cursor.fetchall()

  if result_query:

    patient_msg, text_msg, time_msg = zip(*result_query)

    # looking for biological parameters
    cursor.execute('SELECT parametri_rilevati.id_paziente, parametri_rilevati.valore, parametri.nome \
                    AS nome_parametro, parametri_rilevati_gruppo.data AS nome_gruppo \
                    FROM parametri_rilevati JOIN parametri \
                    ON (parametri_rilevati.id_parametro = parametri.id_parametro) \
                    JOIN parametri_rilevati_gruppo \
                    ON (parametri_rilevati.id_parametro_rilevato_gruppo = parametri_rilevati_gruppo.id_parametro_rilevato_gruppo) \
                    JOIN parametri_gruppi ON (parametri_gruppi.id_gruppo_parametro = parametri_rilevati_gruppo.id_gruppo) \
                    WHERE parametri_rilevati_gruppo.data <= "{0}"'.format(now))

    # patient_bio, patient_bioval, patient_param, bio_time = zip(*self._cursor.fetchall())

    result_query = defaultdict(dict)
    for patient_bio, patient_bioval, patient_param, bio_time in cursor.fetchall():
      result_query[patient_bio][patient_param] = float(patient_bioval)
      result_query[patient_bio]['storage_time'] = bio_time

    data_to_process = [None] * len(patient_msg)

    for i, patient in enumerate(patient_msg):
      for bio_patient, bio_params in result_query.items():
        if patient == bio_patient:
          data_to_process[i] = (text_msg[i], patient_msg[i], bio_params, time_msg[i])
          break

      if data_to_process[i] is None:
        data_to_process[i] = (text_msg[i], patient_msg[i], None, time_msg[i])

    # start to process

    text_msg, patient_id, bio_params, time_msg = zip(*data_to_process)

    score = net.predict(text_msg, bio_params, dictionary, binning=False)

    results_to_write = [(Id, txt, time, s) for s, Id, time, txt in zip(score, patient_id, time_msg, text_msg)]

    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'floating_score_history.csv')), 'w', encoding='utf-8') as fp:
      fp.write('patient_id,text_message,time,floating_score\n')

      for p_id, txt, time, s in results_to_write:
        txt = txt.replace('\n', '').replace('\r', '')
        fp.write(','.join([str(p_id), '"' + txt + '"', time.strftime("%m/%d/%Y_%H:%M:%S"), str(s)]) + '\n')

