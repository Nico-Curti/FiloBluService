#!/usr/bin/env python

import os
import sys
import win32event
import win32service
import win32serviceutil
from database import FiloBluDB

__author__ = 'Nico Curti'
__email__ = 'nico.curti2@unibo.it'
__package__ = 'Filo Blu Service'


# global variables that must be set and used in the following class
# The paths are relative to the current python file
DICTIONARY = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'DB_parole_filter.dat'))
MODEL = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'SAna_DNN_trained_0_weights.h5'))
CONFIGFILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'config.json'))
LOGFILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs', 'filo_blu_service.log'))


class FiloBluService (win32serviceutil.ServiceFramework):
  """
  FiloBluService class object (inheritance from win32serviceutil)

  The class implements a Windows service called 'FiloBluService' (name that can be found in Task Manager
  after the install of the service).
  The service can be enabled running the current file with the 'install' command line parameter.
  Please make sure to 'update' the service after each editing.

  The constructor of the object has also a FiloBluDB member object to allow the connection to the central
  database (the FiloBluDB object class can be found in the 'database.py' file).

  The logfile and the configfile used in the constructor must be global variables (see the default variables
  at the beginning of the current file).

  The service start calling a time-dependent series of function (public members of FiloBluDB object) as
  independet threads.
  Then the main loop begins until the 'stop' command of the service is given.
  """


  # Service name in Task Manager
  _svc_name_ = "FiloBluService"
  # Service name in SERVICES Desktop App and Description in Task Manager
  _svc_display_name_ = "Filo Blu Service"
  # Service description in SERVICES Desktop App
  _svc_description_ = "Filo Blu processing message Service"


  def __init__(self, args):
    """
    FiloBluService constructor.
    The variable CONFIGFILE and LOGFILE must be global variables!
    The 'args' variable is used to start/stop/update/install the service and it must be the
    first sys.argv variable.
    """
    self._db = FiloBluDB(CONFIGFILE, LOGFILE, MODEL, DICTIONARY)

    win32serviceutil.ServiceFramework.__init__(self, args)
    self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)


  def SvcStop(self):
    """
    FiloBluService stop function.
    It just stop the service and return.
    To call this function the current python script must be run as 'python filoblu_service.py stop'.
    There are not other alternatives up to now.
    """

    # tell the SCM we're shutting down
    self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
    # fire the stop event
    win32event.SetEvent(self.hWaitStop)


  def SvcDoRun(self):
    """
    FiloBluService run function.
    This function is called after the 'start' command (python filoblu_service.py start) and must be called
    after the installation of the service (python filoblu_service.py install).
    Do not try to call this function explicitally because it is automatically run after the 'start'.

    Before the main loop of the service (while rc != win32event.WAIT_OBJECT_0) a series of timer-function
    are called.
    The function are public members of the FiloBluDB member object and are all decorated with a time_interval
    function (see misc.py for the decorators implementation).
    This function spawn a thread for each one and the function is asynchronously called at each time interval
    set in the function definition (see database.py for the functions implementation).

    The 'callback_last_messages' make a query to the central db and it processes the last messages found in
    the time interval with the neural network framework; then it re-write the results in the db.
    The time interval of this function must be set according to the execution time of the processing step and
    to the application needs.

    The 'callback_clear_log' clear the log file to a better memory management.
    This second callback must be called with a larger time interval (example each day).
    """

    self._db.callback_last_messages()
    self._db.callback_clear_log()

    self._db.get_logger.info('FILO BLU Service: STARTING UP')

    rc = None
    # if the stop event hasn't been fired keep looping
    while rc != win32event.WAIT_OBJECT_0:
      rc = win32event.WaitForSingleObject(self.hWaitStop, 990)

    self._db.get_logger.info('FILO BLU Service: SHUTDOWN')


def parse_args(argv):
  """
  Just a simple parser of the command line.
  There are not required parameters because the scripts can run also with the
  set of default variables set at the beginning of this script.

  -----

  Variables

    argv : list - The list of sys.argv after the '--' separator token

  Return

    args : object - Each member of the object identify a different command line argument (properly casted)
  """


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
  parser.add_argument('--dictionary',
                      dest='dictionary',
                      type=str,
                      required=False,
                      action='store',
                      help='Word dictionary sorted by frequency',
                      default=DICTIONARY
                      )

  args = parser.parse_args(argv)
  args.config = os.path.abspath(args.config)
  args.logs = os.path.abspath(args.logs)
  args.model = os.path.abspath(args.model)
  args.dictionary = os.path.abspath(args.dictionary)

  return args


def print_help():
  """
  Try to catch all possible errors with a simple
  usage function.
  """
  print ('Usage:')
  print ('python filoblu_service.py [install|start|update|stop] -- [--config config_filename] [--logs logs_filename] [--model network_model_filename] [--dictionary words_dictionary_file]')


if __name__ == '__main__':

  # Understand the right call of the script
  if len(sys.argv) <= 1:
    print_help()
    sys.exit(1)

  try:

    # Split the argument command line in two parts: the first is related to the windows service application
    # and the second to the possible arguments to override the default ones.

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
    DICTIONARY = args.dictionary

    if argv[1] in ['start', 'update']:
      print ('Service used with the following arguments:')
      print ('  CONFIGFILE = {}'.format(CONFIGFILE))
      print ('  LOGFILE    = {}'.format(LOGFILE))
      print ('  MODEL      = {}'.format(MODEL))
      print ('  DICTIONARY = {}'.format(DICTIONARY))

  # catch all the exception
  except:

    if argv[1] in ['start', 'update']:
      print ('Service used with default arguments:')
      print ('  CONFIGFILE = {}'.format(CONFIGFILE))
      print ('  LOGFILE    = {}'.format(LOGFILE))
      print ('  MODEL      = {}'.format(MODEL))
      print ('  DICTIONARY = {}'.format(DICTIONARY))

  # Create the logs directory if it does not exist.
  log_directory = os.path.dirname(LOGFILE)
  os.makedirs(log_directory, exist_ok=True)

  # run the service
  win32serviceutil.HandleCommandLine(FiloBluService)
