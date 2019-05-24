#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import win32event
import win32service
import win32serviceutil
from datetime import datetime

from subprocess import Popen, PIPE

__author__ = 'Nico Curti'
__email__ = 'nico.curti2@unibo.it'
__package__ = 'Filo Blu Service'


LOGFILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs', 'filo_blu_process_service.log'))

PROCESS_SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), 'process.py'))
PYTHON_INTERPRETER = 'python'

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
  _svc_name_ = "FiloBluService_tf"
  # Service name in SERVICES Desktop App and Description in Task Manager
  _svc_display_name_ = "Filo Blu Service tf"
  # Service description in SERVICES Desktop App
  _svc_description_ = "Filo Blu processing message Service with Tensorflow Support"


  def __init__(self, args):
    """
    FiloBluService constructor.
    The variable CONFIGFILE and LOGFILE must be global variables!
    The 'args' variable is used to start/stop/update/install the service and it must be the
    first sys.argv variable.
    """

    # Create the logs directory if it does not exist.
    self._logfile = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs', 'filo_blu_service.log'))
    log_directory = os.path.dirname(self._logfile)
    os.makedirs(log_directory, exist_ok=True)

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        filename=self._logfile,
                        filemode='w')

    self._logger = logging.getLogger()
    self._logger.addHandler(logging.FileHandler(self._logfile, 'a'))

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
    exit(0)


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

    self._logger.info('FILO BLU Service: STARTING UP')

    rc = None
    process_rc = None
    # if the stop event hasn't been fired keep looping
    while rc != win32event.WAIT_OBJECT_0:

      if process_rc:

        self._logger.error('MSG: {} - EXITCODE: {}'.format(stderr, process_rc))

        try:

          os.rename(LOGFILE, LOGFILE + '.{}_err'.format(int(datetime.now().timestamp())) )
          self._logger.info('FILO BLU Service: RE-START SERVICE')

          process = Popen([PYTHON_INTERPRETER, '-W ignore', PROCESS_SCRIPT, '--logs', LOGFILE], stdout=PIPE, stderr=PIPE)
          _, stderr = process.communicate()
          process_rc = process.returncode

        except Exception as e:

          self._logger.error(e)

        finally:

          process.terminate()
          process.kill()

      else:

        try:

          process = Popen([PYTHON_INTERPRETER, '-W ignore', PROCESS_SCRIPT, '--logs', LOGFILE], stdout=PIPE, stderr=PIPE)
          _, stderr = process.communicate()
          process_rc = process.returncode

        except Exception as e:

          self._logger.error(e)

      self._logger.info('FILO BLU Service: RUN CORRECTLY')

      rc = win32event.WaitForSingleObject(self.hWaitStop, 1000)

    self._logger.info('FILO BLU Service: SHUTDOWN')


if __name__ == '__main__':

  # run the service
  if len(sys.argv) == 1:

    import servicemanager

    servicemanager.Initialize()
    servicemanager.PrepareToHostSingle(FiloBluService)
    servicemanager.StartServiceCtrlDispatcher()

  else:

    win32serviceutil.HandleCommandLine(FiloBluService)
