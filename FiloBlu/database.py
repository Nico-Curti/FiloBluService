#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import glob
import logging
import operator
import mysql.connector
from queue import Queue
from datetime import datetime, timedelta

from misc import repeat_interval

__author__ = 'Nico Curti'
__email__ = 'nico.curti2@unibo.it'
__package__ = 'Filo Blu Database connector'

# the following variables are measured in seconds !!!

DT_READ_DB = 20
DT_PROCESS_MESSAGE = 25
DT_WRITE_SCORE_MESSAGES = 30
DT_LOAD_NEW_WEIGHTS = 24 * 60 * 60 # one day
DT_CLEAR_LOG = 24 * 60 * 60 # one day

DT_BIOLOGICAL_SEARCH = 2 # measured in days (confidence interval for query of biological parameters)

class FiloBluDB(object):

  MAX_SIZE_QUEUE = 100

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

    self._wait = False

    self._logfilename = logfile
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        filename=self._logfilename,
                        filemode='w')
    self._logger = logging.getLogger()
    self._logger.addHandler(logging.FileHandler(self._logfilename, 'a'))
    self._logger.info('DB CONNECTION..')

    # disable matplotlib logging
    mpl_logger = logging.getLogger('matplotlib')
    mpl_logger.setLevel(logging.WARNING)

    try:

      with open(config, 'r', encoding='utf-8') as fp:
        self.config = json.load(fp)

      self._db = mysql.connector.connect(
                                        host = self.config['host'],
                                        user = self.config['username'],
                                        passwd = self.config['password'],
                                        database = self.config['database']
                                        )
      self._logger.info ('CONNECTION DB ESTABLISHED')

      self._cursor = self._db.cursor()
      self._cursor.execute('SHOW columns FROM messaggi')
      self._key_id = map(operator.itemgetter(0), self._cursor)
      self._data = {k : [] for k in self._key_id} # I don't know why but without you the program crash
      self._queue = Queue(maxsize=self.MAX_SIZE_QUEUE)
      self._score = Queue(maxsize=self.MAX_SIZE_QUEUE)

    except Exception as e:

      self.log_error(e)


  @repeat_interval(DT_READ_DB)
  def callback_read_last_messages(self):
    """
    Callback function.
    This function evaluate the current time and it executes a query on the db filtering by the time
    (keyword 'scritto_il').
    This method is tuned over the FiloBluDB format db and the query must be changed if you run on
    different database.
    If some new messages are found the extraction of biological parameters associated to each patient
    is performed considering a time interval (confidence interval for biological variables update) of 2 days.
    The extracted records are then re-organized inside the 'text_msg' variable and processed by the
    neural network algorithm to extract the score values.
    The variables are stored in a queue array for FIFO management of the data.

    The function is called every DT_READ_DB seconds.
    """

    if not self._wait:

      self._logger.info('Calling Callback message')

      try:

        now = datetime.now()
        interval_time = now - timedelta(seconds=DT_READ_DB * 5)

        self._db = mysql.connector.connect(
                                            host = self.config['host'],
                                            user = self.config['username'],
                                            passwd = self.config['password'],
                                            database = self.config['database']
                                          )
        self._cursor = self._db.cursor()

        self._cursor.execute('SELECT id_paziente, testo, scritto_il FROM messaggi WHERE scritto_il < "{0}" AND scritto_il >= "{1}" AND sa_score = 0'.format(now, interval_time))
        #self._cursor.execute('SELECT id_paziente, testo, scritto_il FROM messaggi WHERE scritto_il < "{0}" AND sa_score = 0'.format(now)) # FOR DEBUG
        result_query = self._cursor.fetchall()

        self._logger.info('Found {} messages to process'.format(len(result_query)))

        if result_query:

          patient_msg, text_msg, time_msg = zip(*result_query)

          # looking for biological parameters
          #two_days_ago  = now - timedelta(days=DT_BIOLOGICAL_SEARCH)
          self._cursor.execute('SELECT id_paziente, id_parametro_rilevato, valore FROM parametri_rilevati') # insert time filter
          patient_bio, patient_param, patient_bioval = zip(*self._cursor.fetchall())

          data_to_process = [None] * len(patient_msg)

          for i, patient in enumerate(patient_msg):
            for j, bio_patient in enumerate(patient_bio):
              if patient == bio_patient:
                data_to_process[i] = (text_msg[i], patient_msg[i], patient_param[j], patient_bioval[j], time_msg[i])
              else:
                data_to_process[i] = (text_msg[i], patient_msg[i], None,             None,              time_msg[i])

          self._queue.put(data_to_process) # text + biological values

      except Exception as e:

        self.log_error(e)


  @repeat_interval(DT_PROCESS_MESSAGE)
  def callback_process_messages(self, network, dictionary):
    """
    Callback function.
    This function evaluate the last inserted data in the queue container.
    If there are new data to process the pair of (msg, biological params) are given to the NN
    and the score are stored in an other FIFO containter.

    The function is called every DT_PROCESS_MESSAGE seconds.

    -----------

    Variables
      network: object - the neural network object (as tensorflow model or the numpy one)
      dictionary: dict - a dictionary in which keys are words and value are integer (freq order)
    """

    if not self._wait:

      self._logger.info('Calling Callback process message')

      try:

        if not self._queue.empty():

          # Tensorflow does not work in thread!!! BUG
          #self._score = [42]
          data_to_process = self._queue.get()

          text_msg, patient_id, bio_par, bio_val, time_msg = zip(*data_to_process)

          score = network.predict(text_msg, bio_par, bio_val, dictionary)

          results_to_write = [(Id, time, s) for s, Id, time in zip(score, patient_id, time_msg)]

          self._score.put(results_to_write)

      except Exception as e:

        self.log_error(e)


  @repeat_interval(DT_WRITE_SCORE_MESSAGES)
  def callback_write_score_messages(self):
    """
    Callback function.
    This function write the last scores of messages + biological parameters stored in the self._score queue.
    If there are new score variables to write the db is updated following the assumpion of unique keyword
    identifier given by (patient_id, message_time).
    If there are possible mismatch change the query and the previous process callback according to the right variables

    The function is called every DT_WRITE_SCORE_MESSAGES seconds.
    """

    if not self._wait:

      self._logger.info('Calling Callback write message')

      try:

        if not self._score.empty():

          score = self._score.get()

          for id_paziente, scritto_il, sa_score in score:
            self._cursor.execute('UPDATE messaggi SET sa_score = {0} WHERE id_paziente = {1} AND scritto_il = "{2}"'.format(sa_score, id_paziente, scritto_il))

          self._db.commit()

          self._logger.info('Score last messages: {}'.format(list(map(operator.itemgetter(2), score))) )

########## THIS IS THE BEST SOLUTION BUT IT DOES NOT WORK BECAUSE COLUMNS HAVE NOT DEFAULT VALUES!!!
#          try:
#            self._cursor.executemany('INSERT INTO messaggi (id_account, id_paziente, scritto_il, sa_score) VALUES (0, %s, %s, %s) ON DUPLICATE KEY UPDATE id_paziente=VALUES(id_paziente), scritto_il=VALUES(scritto_il)',
#                                     score)
#            self._db.commit()
#
#            self._logger.info(self._cursor.rowcount, 'Record inserted successfully into "messaggi" table')
#
#            self._logger.info('Score last messages: {}'.format(list(map(operator.itemgetter(2), score))) )
#
#          except mysql.connector.Error as e:
#
#            self._db.rollback()
#            self.log_error('Failed to insert into MySQL table {}'.format(e))

      except Exception as e:

        self.log_error(e)


  # check new weights model every day
  @repeat_interval(DT_LOAD_NEW_WEIGHTS)
  def callback_load_new_weights(self, current_weight_file, update_directory):
    """
    Callback function.
    This callback check if there is a new neural network model in the update_directory.
    The updated model must be a file with .upd extension and it must be put in the
    update_directory (just a single file!!).
    The callback moves the update_file into the older one and set a wait variable to
    "stop" the other threads execution until the main service does not reload the network
    model.

    ---------

    Variables
      - current_weight_file: string - the filename of the current weight file loaded by the network
      - update_directory: string - the directory in which the update_files are located.
    """

    self.logger.info('Calling Callback read new model')

    try:

      update_files = glob.glob(os.path.join(os.path.abspath(update_directory), '*.upd'))

      if len(update_files) > 1:

        self.log_error('Error Callback read new model. Found more than one update file')

      else:

        update_files = update_files[0]
        # move the new file
        os.rename(update_files, current_weight_file)

        self._wait = True

    except Exception as e:

      self.log_error(e)


  @repeat_interval(DT_CLEAR_LOG)
  def callback_clear_log(self):
    """
    Callback function.
    This function clear the current log file and restart the logging on the same file.
    If an error occurs an error message is written in the current logfile and the file
    is saved with the current time (UNIX) in the name.

    The function is called every DT_CLEAR_LOG seconds.
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
    Write exception in the logfile.
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

    ---------

    Return
      - logger type - the private logger member.
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
  from network_model_np import NetworkModel

  config_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'config.json')

  log_directory = os.path.join(os.path.dirname(__file__), '..', 'logs')
  os.makedirs(log_directory, exist_ok=True)

  logfile = os.path.join(log_directory, 'filo_blu_service.log')
  dictionary = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'DB_parole_filter.dat'))
  model = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'SAna_DNN_trained_0_weights.pkl'))

  filoblu = FiloBluDB(config_file, logfile)

  dictionary = read_dictionary(dictionary)
  network = NetworkModel(model)

  filoblu.callback_read_last_messages()
  filoblu.callback_process_messages(network, dictionary)
  filoblu.callback_write_score_messages()

  time.sleep(100)

