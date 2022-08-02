# relecov-platform
[![python_lint](https://github.com/BU-ISCIII/relecov-tools/actions/workflows/python_lint.yml/badge.svg)](https://github.com/BU-ISCIII/relecov-tools/actions/workflows/python_lint.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Django](https://img.shields.io/static/v1?label=Django&message=3.2.10&color=blue?style=plastic&logo=django)](https://github.com/django/django)
[![Python](https://img.shields.io/static/v1?label=Python&message=3.9.10&color=green?style=plastic&logo=Python)](https://www.python.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-v5.0-blueviolet?style=plastic&logo=Bootstrap)](https://getbootstrap.com)
[![version](https://img.shields.io/badge/version-0.0.1-orange?style=plastic&logo=GitHub)](https://github.com/BU-ISCIII/relecov-platform.git)

> THIS REPO IS IN ACTIVE DEVELOPMENT.
## Table of contents

* [Installation](#installation)
* [Documentation](#documentation)

## Installation

## iSkyLIMS docker installation


## Install relecov-platform in your server running ubuntu
Before starting the installation check :
-   You have **sudo privileges** to install the additional software packets that relecov-platform needs.
-   Database (MySQL/MariaDB) is running  
-   Local server configured for sending emails
-   Apache server is running on local server

#### Clone github repository
```bash

cd /opt
sudo git clone https://github.com/BU-ISCIII/relecov-platform.git relecov-platform
```

#### Configuration settings

Copy the initial setting template into a file named install_settings.txt
```bash
cp template_initial_settings.txt initial_settings.txt
```

Open with your favourite editor the configuration file to set your own values for
database ,email settings and the local IP of the server where relecov-platform will run.
```bash

sudo nano install_settings.txt
```

### Run installation script

Relecov-platform is installed on the "/opt" directory. Before start the installation be sure you have sudo priveleges.

Execute the following commands in a linux terminal.

```bash

sudo bash install.sh
```

After installation is completed open you navigator typing "localhost" or the "server local IP".
