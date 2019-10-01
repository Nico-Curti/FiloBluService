| **Authors**  | **Project** |
|:------------:|:-----------:|
| [**N. Curti**](https://github.com/Nico-Curti) <br/> **A. Ciardiello** <br/> [**S. Giagu**](https://github.com/stefanogiagu)  |  **FiloBlu**  |

[![GitHub pull-requests](https://img.shields.io/github/issues-pr/Nico-Curti/FiloBluService.svg?style=plastic)](https://github.com/Nico-Curti/FiloBlu/pulls)
[![GitHub issues](https://img.shields.io/github/issues/Nico-Curti/FiloBluService.svg?style=plastic)](https://github.com/Nico-Curti/FiloBluService/issues)

[![GitHub stars](https://img.shields.io/github/stars/Nico-Curti/FiloBluService.svg?label=Stars&style=social)](https://github.com/Nico-Curti/FiloBluService/stargazers)
[![GitHub watchers](https://img.shields.io/github/watchers/Nico-Curti/FiloBluService.svg?label=Watch&style=social)](https://github.com/Nico-Curti/FiloBluService/watchers)

| [<img src="https://cdn.rawgit.com/physycom/templates/697b327d/logo_unibo.png" width="100px;"/><br /><sub><b>**UNIBO**</b></sub>](https://github.com/UniboDIFABiophysics)<br /> | [<img src="https://upload.wikimedia.org/wikipedia/it/d/d6/Sapienza_stemma.png" width="100px;"/><br /><sub><b>**Sapienza**</b></sub>](https://www.phys.uniroma1.it/fisica/)<br /> | [<img src="http://www.bimind.it/images/logo-it.png" width="100px;"/><br /><sub><b>**BiMind**</b></sub>](http://www.bimind.it/)<br /> |
| :---: | :---: | :---: |


# FiloBlu Service manager

This package is part of the FILOBLU project (*Application of machine learning algorithms to physician-patient communications, within the FILOBLU project*) and was developed by the collaboration between the Physics Department of the University of Bologna and the Physics Department of the University of Rome (*Sapienza*) with the support of [BiMind](http://www.bimind.it/it/) company.
The module implements a windows service application for the processing of medical text messages and biological parameters stored in a central DB. With a neural network processing a score/importance is given to provide a possible reading order to the doctors.

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Authors](#authors)
4. [License](#license)
5. [Acknowledgments](#acknowledgments)

## Prerequisites

The package is intended for use only on a Windows environment and it needs the MySQL support for the database management.
Before install the package pay attention to download the whole set of dependencies or just simple run:

```
pip install -r requirements.txt
```

inside the main folder of the project.
Make sure also to provide a `config.json` file formatted like below in a `data` folder inside the project:

```
{
  "host" : "localhost_or_the_IP_number",
  "username" : "db_username",
  "password" : "db_pwd",
  "database" : "db_name"
}
```

Before start the service pay attention to have the full set of **system** environment variables! Example (with Anaconda3/Miniconda3):

```
C:\Users\UserName\Anaconda3
C:\Users\UserName\Anaconda3\Library\mingw-w64\bin
C:\Users\UserName\Anaconda3\Library\usr\bin
C:\Users\UserName\Anaconda3\Library\bin
C:\Users\UserName\Anaconda3\Scripts
```
and the **MOST** important:

```
C:\Users\UserName\Anaconda3\Lib\site-packages\pywin32_system32
C:\Users\UserName\Anaconda3\Lib\site-packages\win32
```

and make sure to run the service with an Administrator Powershell or just use the `filobluservice.ps1` script provided in the project folder changing the `project_folder` variable.
This script can be also used as StartUp program to refresh and re-enable the service.

In the `scripts` folder a downloader script of the neural network weight file is provided.
The file can be extracted only with a password: if you are interested in using our pre-trained model, please send an email to one of the [authors](https://github.com/Nico-Curti/FiloBluService/blob/master/AUTHORS.md).


## Installation

First of all follow the Prerequisites instructions.
Then you can just use the `filobluservice.ps1` script or run inside the project folder the following commands with an Administrator Powershell:

```
python FiloBlu\filobluservice_np.py install
python FiloBlu\filobluservice_np.py update
python FiloBlu\filobluservice_np.py start
```

By default each 20 seconds the script provides a query to DB and processes the text messages founded and assign to a score value to each (the floating-point results are converted in a integer value in [1, 4] ).
These scores are then written in the DB.

The data management is performed by queue container to avoid the lost of records due to the time intervals.
The service check also for new model updates and in case it restarts automatically the service with the new weights (the file must be set in a precise folder with a `*.upd` extension).

## Authors

* **Nico Curti** [git](https://github.com/Nico-Curti), [unibo](https://www.unibo.it/sitoweb/nico.curti2)
* **Andrea Ciardiello** [uniroma](https://phd.uniroma1.it/web/ANDREA-CIARDIELLO_nP1268232_IT.aspx)
* **Stefano Giagu** [git](https://github.com/stefanogiagu), [uniroma](https://gomppublic.uniroma1.it/Docenti/Render.aspx?UID=9b08c277-5de0-4441-b3a6-d8e27d85e52f)

See also the list of [contributors](https://github.com/Nico-Curti/FiloBlu/contributors) [![GitHub contributors](https://img.shields.io/github/contributors/Nico-Curti/FiloBlu.svg?style=plastic)](https://github.com/Nico-Curti/FiloBlu/graphs/contributors/) who participated in this project.

## License

The `FiloBlu` package is licensed under the MIT "Expat" License. [![License](https://img.shields.io/github/license/mashape/apistatus.svg)](https://github.com/Nico-Curti/FiloBlu/blob/master/LICENSE.md)

### Acknowledgment

Thanks goes to the BiMind company for their collaboration in the development of this project.
A big thank goes to [Alessandro Fabbri](https://github.com/allefabbri) for the important support in the development of the service manager application.
