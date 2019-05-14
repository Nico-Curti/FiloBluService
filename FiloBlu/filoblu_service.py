#!/usr/bin/env python

import os
import win32event
import win32service
import win32serviceutil
from database import FiloBluDB

__author__ = 'Nico Curtix'
__email__ = 'nico.curti2@unibo.it'
__package__ = 'Filo Blu Service'



MODEL = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'weights.pth'))
CONFIGFILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'config.json'))
LOGFILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs', 'filo_blu_service.log'))


class FiloBluService (win32serviceutil.ServiceFramework):
  # Service name in Task Manager
  _svc_name_ = "FiloBluService"
  # Service name in SERVICES Desktop App and Description in Task Manager
  _svc_display_name_ = "Filo Blu Service"
  # Service description in SERVICES Desktop App
  _svc_description_ = "Filo Blu processing message Service"


  def __init__(self, args):

    self._db = FiloBluDB(CONFIGFILE, LOGFILE)

    win32serviceutil.ServiceFramework.__init__(self, args)
    self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)


  def SvcStop(self):
    # tell the SCM we're shutting down
    self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
    # fire the stop event
    win32event.SetEvent(self.hWaitStop)


  def SvcDoRun(self):

    self._db.callback_last_messages()
    self._db.callback_clear_log()

    self._db.get_logger.info('FILO BLU Service: STARTING UP')

    rc = None
    # if the stop event hasn't been fired keep looping
    while rc != win32event.WAIT_OBJECT_0:
      rc = win32event.WaitForSingleObject(self.hWaitStop, 990)

    self._db.get_logger.info('FILO BLU Service: SHUTDOWN')


def parse_args(argv):

  description = "Filo Blu Run Service"

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

  args = parser.parse_args(argv)
  args.config = os.path.abspath(args.config)
  args.logs = os.path.abspath(args.logs)
  args.model = os.path.abspath(args.model)

  return args



if __name__ == '__main__':

  try:

    import sys

    argv = sys.argv
    # split argument list by the '--' separator
    # the first part is related to the windows service arguments
    sys.argv = argv[:argv.index('--')]
    # the second part is related to the parameters given by keywords
    argv = argv[argv.index('--') + 1:]

    args = parser.parse_args(argv)

    CONFIGFILE = args.config
    MODEL = args.model
    LOGFILE = args.logs

    if argv[1] in ['start', 'update']:
      print ('Service used with the following arguments:')
      print ('  CONFIGFILE = {}'.format(CONFIGFILE))
      print ('  LOGFILE    = {}'.format(LOGFILE))
      print ('  MODEL      = {}'.format(MODEL))

  except:
    if argv[1] in ['start', 'update']:
      print ('Service used with default arguments:')
      print ('  CONFIGFILE = {}'.format(CONFIGFILE))
      print ('  LOGFILE    = {}'.format(LOGFILE))
      print ('  MODEL      = {}'.format(MODEL))

  log_directory = os.path.dirname(LOGFILE)
  os.makedirs(log_directory, exist_ok=True)

  win32serviceutil.HandleCommandLine(FiloBluService)

