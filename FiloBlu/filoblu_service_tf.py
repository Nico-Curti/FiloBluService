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


# Service log file ( different for process logfile!! )
LOGFILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs', 'filo_blu_process_service.log'))

PROCESS_SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), 'process.py'))
PYTHON_INTERPRETER = 'python' # or python3

class FiloBluService (win32serviceutil.ServiceFramework):
  """
  FiloBluService class object (inheritance from win32serviceutil)

  The class implements a Windows service called 'FiloBluService' (name that can be found in Task Manager
  after the service installation).
  The service can be enabled running the current file with the 'install' command line parameter.
  Please make sure to 'update' the service after each editing.

  The constructor of the object has also a FiloBluDB member object to allow the connection to the central
  database (the FiloBluDB object class can be found in the 'database.py' file).

  The service starts calling a Popen process since the tensorflow architecture can not run as a service
  in windows applications.
  The processing pipeline is the re-started if something goes wrong in the code.
  In this way there is a second layer of safety to prevent errors/problems.

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
    There are no other alternatives up to now.
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
    Do not try to call this function explicitly because it is automatically run after the 'start'.

    The main loop starts with the check of previous exit code (initially set to None) and if there were problems it
    renames the previous log file with the Unix time to prevent the remotion and it re-start the processing service.

    For the first run the process service is just started ignoring boring warnings and giving to the script the
    right logfile name.

    The service run until some drastically errors occur to the current python script/service

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
