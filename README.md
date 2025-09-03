# relecov-platform

[![python_lint](https://github.com/BU-ISCIII/relecov-tools/actions/workflows/python_lint.yml/badge.svg)](https://github.com/BU-ISCIII/relecov-tools/actions/workflows/python_lint.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Django](https://img.shields.io/static/v1?label=Django&message=3.2.17&color=blue?style=plastic&logo=django)](https://github.com/django/django)
[![Python](https://img.shields.io/static/v1?label=Python&message=3.9.10&color=green?style=plastic&logo=Python)](https://www.python.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-v5.0-blueviolet?style=plastic&logo=Bootstrap)](https://getbootstrap.com)
[![version](https://img.shields.io/badge/version-1.0.0-orange?style=plastic&logo=GitHub)](https://github.com/BU-ISCIII/relecov-platform.git)

> THIS REPO IS IN ACTIVE DEVELOPMENT.
>
> Web application for the **RELECOV Platform**.  
> This README focuses on **RELECOV Platform** setup and the **integration points** with iSkyLIMS.  
> Generic iSkyLIMS steps are referenced to its official LEAME to avoid duplication.

| Component                 | Version | Description                                         |
|--------------------------|---------|-----------------------------------------------------|
| Apache Tomcat            | 8.5+    | Application server, Java Servlet container.         |
| Red Hat Enterprise Linux | 7+      | Operating system (Red Hat distribution).            |
| Microsoft SQL Server     | 2017    | Relational database system (if used externally).    |
| Python                   | 3.10+   | Programming language.                               |
| Django                   | 5.1.6   | Web framework.                                      |

---

## Table of contents

- [1. Installation flow overview](#1-installation-flow-overview)
- [2. System prerequisites](#2-system-prerequisites)
  - [2.1 Base packages](#21-base-packages)

---

# 1. Installation flow overview

1. Host prerequisites (packages, basic services, users/groups, directories and permissions).
2. MySQL/MariaDB: install/start, harden, create DBs and application user.
3. Restore DB dumps (if available) **or** perform a clean install with migrations.
4. Clone repositories: **relecov-platform** and **iSkyLIMS**.
5. Configure `install_settings.txt` in each project.
6. Install (dependencies + application) using `install.sh`.
7. Load initial data (schema, GFF, test data, iSkyLIMS projects/ontologies).
8. Start and validate (web service, Django admin access, smoke tests).

---

# 2. System prerequisites

## 2.1 Base packages

Before you start, ensure:

- You have **sudo privileges** to install required packages.
- Database server (MySQL/MariaDB) is running.
- A local mail server is configured to send emails.
- Apache HTTP server is running.
- System dependencies are installed.

**RedHat/CentOS:**
~~~bash
sudo yum install -y redhat-lsb-core
~~~

**Ubuntu:**
~~~bash
sudo apt update && sudo apt install -y lsb-release
~~~

**pkg-config:**
~~~bash
sudo apt install -y pkgconf
~~~

**MySQL server y cliente (Ubuntu):**
~~~bash
sudo apt install -y mysql-server mysql-client
~~~

---

# 3. Database (MySQL)

If there is no active MySQL server, it will be necessary to create one first.

**Install MySQL (Ubuntu):**
~~~bash
sudo apt install -y mysql-server mysql-client
~~~

**Start SQL server and enable at start-up:**
~~~bash
sudo systemctl start mysql
sudo systemctl enable mysql
~~~

**Check that the server is active:**
~~~bash
systemctl status mysql
~~~

**Example output:**
~~~bash
mysql.service - MySQL Community Server
Loaded: loaded (/lib/systemd/system/mysql.service; enabled; vendor preset: enabled)
Active: active (running) since Wed 2025-01-29 08:36:16 CET; 1 month 17 days ago
Main PID: 1648 (mysqld)
Status: "Server is operational"
Tasks: 46 (limit: 38269)
Memory: 772.4M
CPU: 1d 5h 31min 6.848s
CGroup: /system.slice/mysql.service
└─1648 /usr/sbin/mysqld
~~~

**Create admin credentials:**
~~~bash
sudo mysql_secure_installation
~~~
- Delete test database (`test_database`)
- Disable anonymous users and remote administrator access
- Reload *privilege tables* to apply changes

## 3.1 Creating the Database (once MySQL has been initialised)

**Create RELECOV database:**
~~~bash
sudo mysql -u root -p
~~~

Within the MySQL client:
~~~sql
CREATE DATABASE relecov;
CREATE DATABASE relecovlims;
~~~

**Check if it is created correctly:**
~~~sql
SHOW DATABASES;
~~~

**Create a non-admin user for managing the new databases:**
~~~sql
CREATE USER 'relecov_user'@'localhost' IDENTIFIED BY 'mypassword';
GRANT ALL PRIVILEGES ON relecov.* TO 'relecov_user'@'localhost';
GRANT ALL PRIVILEGES ON relecovlims.* TO 'relecov_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
~~~

**Upload database backup (if applicable):**
~~~bash
sudo mysql -p relecov     < /path/to/relecov-platform_db.sql
sudo mysql -p relecovlims < /path/to/relecov-iskylims_db.sql
~~~

---

# 4. Clone repositories

Now that we have MySQL ready, we can begin installing the platform.

**Clone the latest version of the code:**
~~~bash
git clone git@github.com:BU-ISCIII/relecov-platform.git
git clone git@github.com:BU-ISCIII/iskylims.git
~~~

**Create deployment directories:**
~~~bash
cd /opt
sudo mkdir relecov-platform
sudo mkdir iskylims
sudo chown -R root:www-data iskylims
sudo chown -R dadmin:apache iskylims
sudo chmod 2775 iskylims
~~~

---

# 5. Configuration – `install_settings.txt`

**Copy the configuration template (relecov-platform):**
~~~bash
cp relecov_platform/conf/template_install_settings.txt relecov_platform/install_settings.txt
~~~

## 5.1 Edit `install_settings.txt` – *relecov-platform*
~~~ini
### Installation path
INSTALL_PATH='/opt/relecov-platform'
PROJECT_NAME='relecov_platform'
REQUIRED_MODULES='core dashboard docs'
MIGRATION_MODULES='core dashboard'

### (optional) Python installation path where pip and python executables are located
PYTHON_BIN_PATH='/path/to/bin/python3'  # example: /usr/bin/python3

### Settings required to access database
DB_USER='relecov_user'
DB_PASS='relecov_user-password'  ## The One defined in the ddbb creation in 3.4.3
DB_NAME='relecov'
DB_SERVER_IP='mydatabaseip.isciii.es'  # 'localhost' si fuera solo para uso local
DB_PORT='3306'                         # ejemplo

### Settings required for accessing relecov-platform
LOCAL_SERVER_IP='10.22.140.235'        # example: 172.0.0.1
DNS_URL='relecov-platform.isciiides.es' # Dejarlo vacío si fuera solo para uso local
SUPERUSER='admin'

### Logs settings
LOG_TYPE='symbolic_link'                # can be symbolic_link or regular_folder
LOG_PATH='/var/log/apps/relecov-platform'  # obligatorio si LOG_TYPE='symbolic_link'

# Check whether LOG_PATH exists; if not, create it.
~~~

## 5.2 Edit `install_settings.txt` – *relecov-iskylims*
~~~ini
### Installation path and modules settings
INSTALL_PATH='/opt/iskylims'
REQUIRED_MODULES='core drylab wetlab clinic django_utils'
MIGRATION_MODULES='core drylab wetlab django_utils'
FAKEINITIAL_MODULES='django_utils iSkyLIMS_core iSkyLIMS_wetlab iSkyLIMS_drylab'

### (optional) Python installation path where pip and python executables are located
PYTHON_BIN_PATH='python3'  # example: /opt/python/3.9.6/bin/python3

### Settings required to access database
DB_USER='relecov_user'
DB_PASS='relecov_user-password'  ## The One defined in the ddbb creation in 3.4.3
DB_NAME='relecovlims'
DB_SERVER_IP='mydatabaseip.isciii.es'   # 'localhost' si fuera solo para uso local
DB_PORT='3306'                          # ejemplo

### Settings required for sending emails
EMAIL_HOST_SERVER='localhost'
EMAIL_PORT='25'
EMAIL_HOST_USER='bioinfo'
EMAIL_HOST_PASSWORD=''
EMAIL_USE_TLS='False'

### Settings required for accessing relecov-platform
LOCAL_SERVER_IP='10.22.140.235'         # example: 172.0.0.1
DNS_URL='relecov-iskylims.isciiides.es' # '' si fuera solo para uso local
SUPERUSER='admin'                        # name of the django superuser that will be created

### Logs settings
LOG_TYPE='symbolic_link'                 # can be symbolic_link or regular_folder
LOG_PATH='/var/log/apps/relecov-iskylims'  # obligatorio si LOG_TYPE='symbolic_link'

# Check whether LOG_PATH exists; if not, create it.
~~~

---

# 6. Installation and deployment

## 6.1 Instalation *relecov-platform*

**With preloaded database:**
~~~bash
sudo bash install.sh --upgrade dep
sudo bash install.sh --upgrade app
~~~

**Full installation (without preloaded DB):**
~~~bash
sudo bash install.sh --install full
~~~

## 6.2 Instalation *relecov-iskylims*

**With preloaded database:**
~~~bash
sudo bash install.sh --upgrade dep
sudo bash install.sh --upgrade app
~~~

**Full installation (without preloaded DB):**
~~~bash
sudo bash install.sh --install full --conf install_settings.txt
~~~

## 6.3 Local deployment

~~~bash
source activate env/bin/activate
~~~

**RELECOV-PLATFORM:**
~~~bash
./manage.py runserver 8000
~~~

**RELECOV-ISKYLIMS:**
~~~bash
./manage.py runserver 8001
~~~

---

## 6.4 Deployment in development server

On the development server, run basic hardening and restart Apache:

~~~bash
# 1) Server hardening
sudo /scripts/hardening.sh

# 2) Restart the web service (apache)
sudo systemctl restart httpd
~~~

# 7. Post-installation data upload

Once we have both platforms deployed, we can proceed with the post-installation configuration files directly from the web.

## 7.1 Post-installation files – *Relecov-Platform*

- **Loading `relecov_schema.json`**  
  In *Configuration → SchemaHandling* of the new deployment, it is possible to attach the latest version of [`relecov_schema.json`](https://raw.githubusercontent.com/BU-ISCIII/relecov-tools/main/relecov_tools/schema/relecov_schema.json).

- **Loading the Annotation GFF**
In *Configuration → Annotation* of the new deployment, it is possible to attach the [`GFF`](https://github.com/BU-ISCIII/relecov-platform/blob/develop/conf/NC_045512.2.gff) file.
- **iSkyLIMS verification**
In the admin panel of the new deployment, verify that `ISKYLIMS_SERVER` in `/admin/core/configsetting/` points to `relecov-lims`.

## 7.2 Post-installation files – *Relecov-Iskylims*

- Create **relecovbot** as a user in the admin panel: `/admin/auth/user/`.

### Configure the RELECOV scheme in iSkyLIMS (via web interface)

1. **URL for accessing the WetLab module** (adjust to your environment):  
   `http://----/wetlab` (or equivalent).

2. **Access**  
   Log in to `…/wetlab` with your iSkyLIMS username.

3. **Navigation**  
   Go to: **PARAMETERS SETTINGS → Define Sample projects**.

4. **Create (or locate) the RELECOV project**  
   - If it does not exist, click **Add** and create a project that includes **‘RELECOV’** in the name.  
   - In **Manager**, select **isabel.cuesta** (or the manager defined for your installation).  
   - Save the changes.

5. **Cargar campos desde el esquema («Load batch»)**  
   - Dentro del proyecto RELECOV: **Define fields → Load batch**  
   - **Upload schema**: seleccionar el archivo `relecov_schema.json`.  
   - **Property where to fetch fields**: `classification`  
   - **Seleccionar los valores que se van a filtrar** (deben coincidir con las *Classification* del esquema que quieras cargar). Marca:
     - Identificadores de la base de datos
     - Información de los archivos
     - Información del host
     - Pruebas de diagnóstico de patógenos
     - Recogida y procesamiento de muestras
     - Secuenciación  
   - Confirmar y guardar.

6. **Ontologymap (variable mapping)**  
   Configure the relationships between iSkyLIMS variables to map based on the schema ontology. Go to:  
   `http://…./admin/core/ontologymap/` and adjust, for example:
   - `sample_type` → `SNOMED:703065002`
   - `lab_request` → `GENEPIO:0001159` (submitting_institution)
   - `species` → `SNOMED:410607006` (Organism)
   - `sample_name` → `GENEPIO:0000079` (sequencing_sample_id)
   - `sample_entry_date` → `SNOMED:281271004` (received_date)
   - `collection_sample_date` → `SNOMED:399445004` (sample_collection_date)

7. **Define *Species***  
   Register the different organisms in the schema at `http://…./admin/core/species/`:
   - *Severe acute respiratory syndrome coronavirus 2*
   - *Respiratory syncytial virus*
   - *Influenza virus*

8. **Apply ‘wetlab’**  
   In the **Apps name** section, select **wetlab**.

---

