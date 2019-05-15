#!/usr/bin/env python

import os
import json
import logging
import operator
import mysql.connector
from datetime import datetime, timedelta

from misc import repeat_interval
from process import load_model, read_dictionary, predict

__author__ = 'Nico Curti'
__email__ = 'nico.curti2@unibo.it'
__package__ = 'Filo Blu Database connector'

class FiloBluDB(object):

  def __init__(self, config, logfile, network_weights, word_dictionary):
    """
    FiloBluDB constructor.

    ---------

    Variables
      - config : string - config file in json fmt. The file must contains the following fields:
                            "host" : "localhost_or_the_IP_number",
                            "username" : "db_username",
                            "password" : "db_pwd",
                            "database" : "db_name"

      - logfile : string - log filename in which the stdout and stderr are dumped.
    """

    self.logfilename = logfile
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        filename=self.logfilename,
                        filemode='w')
    self.logger = logging.getLogger()
    self.logger.addHandler(logging.FileHandler(self.logfilename, 'a'))
    self.logger.info('DB CONNECTION..')

    try:

      with open(config, 'r') as fp:
        config = json.load(fp)

      self.db = mysql.connector.connect(
                                        host = config['host'],
                                        user = config['username'],
                                        passwd = config['password'],
                                        database = config['database']
                                        )
      self.logger.info ('CONNECTION DB ESTABLISHED')

      self.cursor = self.db.cursor()
      self.cursor.execute('SHOW columns FROM messaggi')
      message_id = map(operator.itemgetter(0), self.cursor)
      self.data = {k : [] for k in message_id}

    except Exception as e:

      self.logger.error(e)
      logging.shutdown()
      os.rename(self.logfilename, self.logfilename + '.{}_err'.format(int(datetime.now().timestamp())) )
      exit(1)

    self.logger.info('LOADING PROCESSING MODEL...')

    try:

      self.net = load_model(network_weights)
      self.logger.info('MODEL LOADED')

    except Exception as e:

      self.logger.error(e)
      logging.shutdown()
      os.rename(self.logfilename, self.logfilename + '.{}_err'.format(int(datetime.now().timestamp())) )
      exit(1)

    self.logger.info('LOADING WORD DICTIONARY...')

    try:

      self.dictionary = read_dictionary(word_dictionary)
      self.logger.info('DICTIONARY LOADED')

    except Exception as e:

      self.logger.error(e)
      logging.shutdown()
      os.rename(self.logfilename, self.logfilename + '.{}_err'.format(int(datetime.now().timestamp())) )
      exit(1)


  def execute(self, query):
    """
    Test function to execute a simple query without filters.
    This function is useful for MySQL beginners.

    ---------

    Variables
      - query : string - text of the query in MySQL fmt.

    Return
      - list type - the result of the query
    """

    self.cursor.execute(query)
    return list(self.cursor)


  # read new text message and process them every 2 seconds
  @repeat_interval(2)
  def callback_last_messages(self):
    """
    Callback function.
    This function evaluate the current time and executes a query on the db filtering by the time
    (keyword 'scritto_il').
    This method is tuned over the FiloBluDB format and the query must be changed if you run on
    different database.
    The extracted records are then re-organized inside the 'data' variable and processed by the
    neural network algorithm to extract the score values.
    The results are then re-written in the db.
    # miss score description

    The function is called every 2 seconds.
    Change the value in the decorator for a different clock time and pay attention to change
    the query for the time in the db (see the comments below).
    """

    self.logger.info('Calling Callback message')

    try:

      now = datetime.now()
      ########## pay attention to modify this line if you change the repeat interval!!!!
      timer = now - timedelta(seconds=2)

      self.data.fromkeys(self.data, [])

      self.cursor.execute('SELECT * from messaggi WHERE scritto_il < "{0}" AND scritto_il >= "{1}"'.format(now, timer))
      records = self.cursor.fetchall()

      self.logger.info('Found {} messages to process'.format(len(records)))

      for rec in records:
        for r, k in zip(rec, self.data.keys()):
          self.data[k].append(r)

      if self.data['testo']:
        score_predicted = predict(self.net, self.data['testo'], self.dictionary)
        self.logger.info('Score estimated: {}'.format(score_predicted.ravel()))

    except Exception as e:

      self.logger.error(e)
      logging.shutdown()
      os.rename(self.logfilename, self.logfilename + '.{}_err'.format(int(datetime.now().timestamp())) )
      exit(1)


  # clear log every day
  @repeat_interval(24 * 60 * 60)
  def callback_clear_log(self):
    """
    Callback function.
    This function clear the current log file and restart the logging on the same file.
    If an error occurs an error message is written in the current logfile and the file
    is saved with the current time (UNIX) in the name.
    The service is stopped if an error occures (this option can be deleted removing the exit at the
    end of the exception catch).

    The function is called every day (24 hours * 60 minutes * 60 seconds).
    Change the value in the decorator for a different clock time.
    """

    self.logger.info('Calling Callback clear log')

    try:

      logging.shutdown()
      logging.basicConfig(level=logging.DEBUG,
                          format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                          datefmt='%m-%d %H:%M:%S',
                          filename=self.logfilename,
                          filemode='w')
      self.logger = logging.getLogger()
      self.logger.addHandler(logging.FileHandler(self.logfilename, 'a'))

    except Exception as e:

      self.logger.error(e)
      logging.shutdown()
      os.rename(self.logfilename, self.logfilename + '.{}_err'.format(int(datetime.now().timestamp())) )
      exit(1)



  @property
  def get_logger(self):
    """
    Class member to obtain the logger variable.
    It can be used to extract the logger outside the class functions.
    """
    return self.logger



  @property
  def message_ID(self):
    """
    Class member to extract the full set of the available keys in the data member dictionary.

    ---------

    Return
      - list type - the full set of available keys.
    """
    return list(self.data.keys())



  def __getitem__(self, key):
    """
    Overload of the [] operator.

    ---------

    Variable
      - key : string - key argument for the data member dictionary. The full set of possible keys can be
                       obtained by the 'message_ID' member of the class.

    Return
      - list type - the object stored in the data object at the given key
    """
    return self.data[key]




if __name__ == '__main__':

  import time

  config_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'config.json')

  log_directory = os.path.join(os.path.dirname(__file__), '..', 'logs')
  os.makedirs(log_directory, exist_ok=True)

  logfile = os.path.join(log_directory, 'filo_blu_service.log')
  dictionary = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'DB_parole_filter.dat'))
  model = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'SAna_DNN_trained_0_weights.h5'))


  filoblu = FiloBluDB(config_file, logfile, model, dictionary)

  data = filoblu.callback_last_messages()

  time.sleep(10)

  print(filoblu.message_ID)
  print(filoblu['testo'])



