#!/usr/bin/env python

import os
import json
import logging
import operator
import mysql.connector
from datetime import datetime, timedelta

from misc import repeat_interval

__author__ = 'Nico Curtix'
__email__ = 'nico.curti2@unibo.it'
__package__ = 'Filo Blu Database connector'

class FiloBluDB(object):

  def __init__(self, config, logfile):

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
      os.rename(self.logfilename, self.logfilename + '.{}_err'.format(datetime.now()))
      exit(1)



  def execute(self, query):

    self.cursor.execute(query)
    return list(self.cursor)


  # read new text message and process them every 2 seconds
  @repeat_interval(2)
  def callback_last_messages(self):

    self.logger.info('Calling Callback message')

    try:

      now = datetime.now()
      ########## pay attention to modify this line if you change the repeat interval!!!!
      timer = now - timedelta(seconds=2)

      self.data.fromkeys(self.data, [])

      self.cursor.execute('SELECT * from messaggi WHERE scritto_il < "{}"'.format(timer))
      records = self.cursor.fetchall()

      for rec in records:
        for r, k in zip(rec, self.data.keys()):
          self.data[k].append(r)
      return self.data

    except Exception as e:

      self.logger.error(e)
      logging.shutdown()
      os.rename(self.logfilename, self.logfilename + '.{}_err'.format(datetime.now()))
      exit(1)


  # clear log every day
  @repeat_interval(24 * 60 * 60)
  def callback_clear_log(self):

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
      os.rename(self.logfilename, self.logfilename + '.{}_err'.format(datetime.now()))
      exit(1)



  @property
  def get_logger(self):
    return self.logger



  @property
  def message_ID(self):
    return list(self.data.keys())



  def __getitem__(self, key):
    return self.data[key]




if __name__ == '__main__':

  config_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'config.json')

  log_directory = os.path.join(os.path.dirname(__file__), '..', 'logs')
  os.makedirs(log_directory, exist_ok=True)

  logfile = os.path.join(log_directory, 'filo_blu_service.log')

  filoblu = FiloBluDB(config_file, logfile)

  data = filoblu.callback_last_messages()

  print(filoblu.message_ID)
  print(filoblu['testo'])



