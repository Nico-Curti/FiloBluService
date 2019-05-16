#!/usr/bin/env python

import os
import json
import logging
import operator
import mysql.connector
from datetime import datetime, timedelta

from misc import repeat_interval

__author__ = 'Nico Curti'
__email__ = 'nico.curti2@unibo.it'
__package__ = 'Filo Blu Database connector'

class FiloBluDB(object):

  def __init__(self, config, logfile):
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

    self._logfilename = logfile
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        filename=self._logfilename,
                        filemode='w')
    self._logger = logging.getLogger()
    self._logger.addHandler(logging.FileHandler(self._logfilename, 'a'))
    self._logger.info('DB CONNECTION..')

    try:

      with open(config, 'r') as fp:
        config = json.load(fp)

      self._db = mysql.connector.connect(
                                        host = config['host'],
                                        user = config['username'],
                                        passwd = config['password'],
                                        database = config['database']
                                        )
      self._logger.info ('CONNECTION DB ESTABLISHED')

      self._cursor = self._db.cursor()
      self._cursor.execute('SHOW columns FROM messaggi')
      self._key_id = map(operator.itemgetter(0), self._cursor)
      self._data = {k : [] for k in self._key_id}
      self._score = None

    except Exception as e:

      self.log_error(e)



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

    self._cursor.execute(query)
    return list(self._cursor)


  # read new text message and process them every 2 seconds
  @repeat_interval(2)
  def callback_read_last_messages(self):
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

    self._logger.info('Calling Callback message')

    try:

      now = datetime.now()
      ########## pay attention to modify this line if you change the repeat interval!!!!
      timer = now - timedelta(seconds=2)

      self._cursor.execute('SELECT * from messaggi WHERE scritto_il < "{0}" AND scritto_il >= "{1}"'.format(now, timer))
      #self._cursor.execute('SELECT * from messaggi WHERE scritto_il < "{0}"'.format(now)) # FOR DEBUG
      records = self._cursor.fetchall()

      if records:
        self._logger.info('Found {} messages to process'.format(len(records)))
        self._data = {k : [] for k in self._key_id}

        for rec in records:
          for r, k in zip(rec, self._key_id):
            self._data[k].append(r)

    except Exception as e:

      self.log_error(e)


  def callback_process_messages(self, network, dictionary):
    """
    Callback function.
    This function evaluate the message stored in the self.data variable

    The function is called every second.
    """

    self._logger.info('Calling Callback process message')

    try:

      if self._data:

        # Tensorflow does not work in thread!!! BUG
        self._score += network.predict(self._data['testo'], dictionary)
        self._data.clear()

    except Exception as e:

      self.log_error(e)

  @repeat_interval(1)
  def callback_write_score_messages(self):
    """
    Callback function.
    This function write the scores of messages stored in the self.score variable

    The function is called every second.
    """

    self._logger.info('Calling Callback write message')

    try:

      if self._score:
        self._logger.info('Score last messages: {}'.format(self._score))
        self._score = None

    except Exception as e:

      self.log_error(e)


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

    self._logger.info('Calling Callback clear log')

    try:

      logging.shutdown()
      logging.basicConfig(level=logging.DEBUG,
                          format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                          datefmt='%m-%d %H:%M:%S',
                          filename=self._logfilename,
                          filemode='w')
      self._logger = logging.getLogger()
      self._logger.addHandler(logging.FileHandler(self._logfilename, 'a'))

    except Exception as e:

      self.log_error(e)


  def log_error(self, exception):
    """
    Write exception in logfile and exit.
    The logfile with the error is rename with the UNIX time to prevent clear log callback
    """
    self._logger.error(exception)
    logging.shutdown()
    os.rename(self._logfilename, self._logfilename + '.{}_err'.format(int(datetime.now().timestamp())) )


  @property
  def get_logger(self):
    """
    Class member to obtain the logger variable.
    It can be used to extract the logger outside the class functions.
    """
    return self._logger



  @property
  def message_ID(self):
    """
    Class member to extract the full set of the available keys in the data member dictionary.

    ---------

    Return
      - list type - the full set of available keys.
    """
    return list(self._key_id)



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
    return self._data[key]




if __name__ == '__main__':

  import time

  from misc import read_dictionary
  from network_model import NetworkModel

  config_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'config.json')

  log_directory = os.path.join(os.path.dirname(__file__), '..', 'logs')
  os.makedirs(log_directory, exist_ok=True)

  logfile = os.path.join(log_directory, 'filo_blu_service.log')
  dictionary = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'DB_parole_filter.dat'))
  model = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'SAna_DNN_trained_0_weights.h5'))

  filoblu = FiloBluDB(config_file, logfile)

  dictionary = read_dictionary(dictionary)
  network = NetworkModel(model)

  filoblu.callback_read_last_messages()
  filoblu.callback_process_messages(network, dictionary)
  filoblu.callback_write_score_messages()

  time.sleep(10)

  #print(filoblu.message_ID)
  #print(filoblu['testo'])



