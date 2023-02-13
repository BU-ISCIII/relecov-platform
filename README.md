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
* [Upgrade new release](#upgrade-to-new-release)
* [Documentation](#documentation)

# Installation

## Relecov docker installation

SOME MODIFICATIONS

## Install relecov-platform in your server (RedHat / CentOs / Ubuntu)
Before starting the installation check :
-   You have **sudo privileges** to install the additional software packets that relecov-platform needs.
-   Database (MySQL/MariaDB) is running
-   Local server configured for sending emails
-   Apache server is running on local server
-   Dependencies:
     - lsb_release:
     RedHat/CentOS: ```yum install redhat-lsb-core```

### Create relecov database and grant permissions

1. Create a new database named "relecov" (this is mandatory)
2. Create a new user with permission to read and modify that database.
3. Write down user, passwd and db server info.


### Clone github repository
Open a linux terminal and move to a directory where relecov code will be downloaded

```bash
cd <your personal folder>
git clone https://github.com/BU-ISCIII/relecov-platform.git relecov-platform
cd relecov_platform
```

### Configuration settings

Copy the initial setting template into a file named install_settings.txt
```bash
cp conf/template_install_settings.txt initial_settings.txt
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

## Install nextstrain

The Nextstrain CLI ties together all necesary pieces to provide a consistent way to run pathogen workflows, access Nextstrain tools like Augur and Auspice across computing environments such as Docker, Conda, and AWS Batch, and publish datasets to nextstrain.org.

# Download installer
Move to the installation path and download installer
```
mkdir -p /opt/nextstrain
cd /opt/nextstrain
curl -fsSL --proto '=https' https://nextstrain.org/cli/installer/linux > nexstrain_installer_$(date "+%Y%m%d").sh
```
Set NEXSTRAIN_HOME env variable and run installer
```
export NEXTSTRAIN_HOME=/opt/nextstrain
bash nexstrain_installer_$(date "+%Y%m%d").sh
``` 

Set conda as default run-time.This will install the nexstrain conda env with all deps using micromamba.
```
/opt/nextstrain/cli-standalone/nextstrain setup --set-default conda
```

Copy service file to `/usr/lib/systemd/system`
```
cp ./conf/nextstrain.service /usr/lib/systemd/system
```

Copy auspice dataset to datasets folder. This contains all the data that should be rendered by nextstrain app. This is created using the [nexstrain_relecov workflow](https://github.com/BU-ISCIII/nexstrain_relecov)
```
mkdir -p /opt/nextstrain/dataset/sars-cov-2
cp -r /path/to/auspice /opt/nextstrain/dataset/sars-cov-2
```

# Upgrade to new release

### Update github repository
Open a linux terminal and move to a directory where relecov code was download during installation

```bash
cd < folder where relecov code was download >
git pull
cd relecov_platform
```
### Run upgrade script

Execute the following command in a linux terminal.

```bash

sudo bash install.sh upgrade
```


# Documentation