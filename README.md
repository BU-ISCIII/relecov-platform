# relecov-platform
[![python_lint](https://github.com/BU-ISCIII/relecov-tools/actions/workflows/python_lint.yml/badge.svg)](https://github.com/BU-ISCIII/relecov-tools/actions/workflows/python_lint.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Django](https://github.com/django/django)](https://github.com/django/django)

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

#### Configuration settings

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
