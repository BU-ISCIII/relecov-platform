# RELECOV-PLATFORM

[![Apache Tomcat](https://img.shields.io/static/v1?label=Apache%20Tomcat&message=8.5%2B&logo=apachetomcat&color=F8DC75&style=plastic)](https://tomcat.apache.org/)
[![Red Hat Enterprise Linux](https://img.shields.io/static/v1?label=Red%20Hat%20Enterprise%20Linux&message=7%2B&logo=redhat&color=EE0000&style=plastic)](https://www.redhat.com/)
[![Microsoft SQL Server](https://img.shields.io/static/v1?label=Microsoft%20SQL%20Server&message=2017&logo=microsoftsqlserver&color=CC2927&style=plastic)](https://www.microsoft.com/sql-server)
[![Python](https://img.shields.io/static/v1?label=Python&message=3.10%2B&logo=python&color=3776AB&style=plastic)](https://www.python.org/)
[![Django](https://img.shields.io/static/v1?label=Django&message=5.1.6&logo=django&color=092E20&style=plastic)](https://www.djangoproject.com/)

| Componente                 | Versión | Descripción                                     |
|---------------------------|---------|-------------------------------------------------|
| Apache Tomcat             | 8.5+    | Servidor de aplicaciones, contenedor Java Servlet. |
| Red Hat Enterprise Linux  | 7+      | Sistema operativo, distribución Red Hat.        |
| Microsoft SQL Server      | 2017    | Sistema de gestión de base de datos relacional. |
| Python                    | 3.10+   | Lenguaje de programación.                       |
| Django                    | 5.1.6   | Framework web.                                  |

---

## Índice

- [1. Resumen del flujo (orden correcto)](#1-resumen-del-flujo-orden-correcto)
- [2. Pre-requisitos del sistema](#2-pre-requisitos-del-sistema)
  - [2.1 Paquetes base](#21-paquetes-base)
- [3. Base de datos (MySQL)](#3-base-de-datos-mysql)
  - [3.1 Creación de la Base de Datos](#31-creación-de-la-base-de-datos-una-vez-inicializado-mysql)
- [4. Clonar repositorios](#4-clonar-repositorios)
- [5. Configuración – install_settings.txt](#5-configuración--install_settingstxt)
  - [5.1 Editar install_settings.txt – relecov-platform](#51-editar-install_settingstxt--relecov-platform)
  - [5.2 Editar install_settings.txt – relecov-iskylims](#52-editar-install_settingstxt--relecov-iskylims)
- [6. Instalación y despliegue](#6-instalación-y-despliegue)
  - [6.1 Instalación relecov-platform](#61-instalación-relecov-platform)
  - [6.2 Instalación relecov-iskylims](#62-instalación-relecov-iskylims)
  - [6.3 Despliegue en local](#63-despliegue-en-local)
  - [6.4 Despliegue en desarrollo (servidor)](#64-despliegue-en-desarrollo-servidor)
- [7. Carga de datos posteriores a la instalación](#7-carga-de-datos-posteriores-a-la-instalación)
  - [7.1 Relecov-Platform](#71-archivos-post-instalación--relecov-platform)
  - [7.2 Relecov-Iskylims](#72-archivos-post-instalación--relecov-iskylims)
- [8. Arranque y validación básica](#8-arranque-y-validación-básica)

---


# 1. Resumen del flujo (orden correcto)

- Pre-requisitos del host (paquetes, servicios básicos, usuarios/grupos, carpetas y permisos).
- MySQL/MariaDB: instalación/arranque, hardening, creación de BBDD y usuario.
- Restauración desde dump (si aplica) o instalación “limpia” con migraciones.
- Clonado de repositorios: `relecov-platform` y `iskylims`.
- Configuración de `install_settings.txt` en cada proyecto.
- Instalación (dependencias + aplicación) mediante `install.sh`.
- Carga de datos (schema, GFF, test data, proyectos de iSkyLIMS, ontologías).
- Arranque y validación (servicio web, acceso Django admin, pruebas mínimas).

---

# 2. Pre-requisitos del sistema

## 2.1 Paquetes base

Antes de iniciar la instalación, asegúrate de que:

- Tienes privilegios de `sudo` para instalar paquetes requeridos.
- El servidor de base de datos (MySQL/MariaDB) está en ejecución.
- El servidor de correo está configurado para enviar emails.
- El servidor Apache está en ejecución.
- Dependencias del sistema están instaladas.
- **Además, revisa los requisitos previos específicos de iSkyLIMS**: [LEAME → Requisitos previos](https://github.com/BU-ISCIII/iskylims/blob/main/LEAME.md#requisitos-previos).  

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

# 3. Creación de la Base de Datos (una vez inicializado MySQL)

**Crear base de datos RELECOV:**
~~~bash
sudo mysql -u root -p
~~~

Dentro del cliente MySQL:
~~~sql
CREATE DATABASE relecov;
CREATE DATABASE relecovlims;
~~~

**Ver si está creada correctamente:**
~~~sql
SHOW DATABASES;
~~~

**Crear un usuario no-admin para manejo de las nuevas bases de datos:**
~~~sql
CREATE USER 'relecov_user'@'localhost' IDENTIFIED BY 'mypassword';
GRANT ALL PRIVILEGES ON relecov.* TO 'relecov_user'@'localhost';
GRANT ALL PRIVILEGES ON relecovlims.* TO 'relecov_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
~~~

**Cargar backup de las Bases de Datos:**
~~~bash
sudo mysql -p relecov     < /path/to/relecov-platform_db.sql
sudo mysql -p relecovlims < /path/to/relecov-iskylims_db.sql
~~~

---

# 4. Clonar repositorios

Ahora que ya tenemos MySQL preparado, podemos comenzar con la instalación de la plataforma.

**Clonar la última versión del código:**
~~~bash
git clone git@github.com:BU-ISCIII/relecov-platform.git
~~~

Para _iSkyLIMS_, sigue: [Clonar el repositorio de GitHub](https://github.com/BU-ISCIII/iskylims/blob/main/LEAME.md#clonar-el-repositorio-de-github).

**Crear directorios de despliegue:**
~~~bash
cd /opt
sudo mkdir relecov-platform
sudo mkdir iskylims
sudo chown -R root:www-data iskylims
sudo chown -R dadmin:apache iskylims
sudo chmod 2775 iskylims
~~~

---

# 5. Configuración – `install_settings.txt`

**Copiar el template de configuración (relecov-platform):**
~~~bash
cp relecov_platform/conf/template_install_settings.txt relecov_platform/install_settings.txt
~~~

## 5.1 Editar `install_settings.txt` – *relecov-platform*
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

## 5.2 Editar `install_settings.txt` – *relecov-iskylims*
Configura iSkyLIMS según [Configuración de ajustes](https://github.com/BU-ISCIII/iskylims/blob/main/LEAME.md#configuración-de-ajustes). **Nota**: ajusta `DB_NAME` al usado en tu entorno RELECOV (`relecovlims`) y mantén la misma IP/host que usará relecov-platform.
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

# 6. Instalación y despliegue

## 6.1 Instalación *relecov-platform*

~~~bash
sudo bash install.sh --upgrade dep
sudo bash install.sh --upgrade app
~~~

## 6.2 Instalación *relecov-iskylims*

~~~bash
sudo bash install.sh --upgrade dep
sudo bash install.sh --upgrade app
~~~

## 6.3 Despliegue
En el servidor de desarrollo ejecutar el endurecimiento básico y reiniciar Apache:

~~~bash
# 1) Endurecimiento del servidor (hardening)
sudo /scripts/hardening.sh

# 2) Reiniciar el servicio web
sudo systemctl restart httpd
~~~

# 7. Carga de datos posteriores a la instalación

Una vez tenemos las dos plataformas desplegadas podemos proceder con los archivos de configuración post-instalación directamente desde la web.

## 7.1 Archivos Post-instalación – *Relecov-Platform*

- **Carga del `relecov_schema.json`**  
  En *Configuration → SchemaHandling* del nuevo despliegue es posible adjuntar el [`relecov_schema.json`](https://raw.githubusercontent.com/BU-ISCIII/relecov-tools/main/relecov_tools/schema/relecov_schema.json) de la última versión.

- **Carga del GFF de Annotation**  
  En *Configuration → Annotation* del nuevo despliegue es posible adjuntar el archivo [`GFF`](https://github.com/BU-ISCIII/relecov-platform/blob/develop/conf/NC_045512.2.gff).
- **Comprobación de iSkyLIMS**  
  En el panel de admin del nuevo despliegue, comprobar que `ISKYLIMS_SERVER` en `/admin/core/configsetting/` apunta a `relecov-lims`.

## 7.2 Archivos Post-instalación – *Relecov-Iskylims*

- Crear **relecovbot** como usuario en el panel de admin: `/admin/auth/user/`.

### Configurar el esquema RELECOV en iSkyLIMS (vía interfaz web)

1. **URL de acceso al módulo WetLab** (ajusta al entorno):  
   `http://----/wetlab` (o equivalente).

2. **Acceso**  
   Entrar en `…/wetlab` con tu usuario de iSkyLIMS.

3. **Navegación**  
   Ir a: **PARAMETERS SETTINGS → Define Sample projects**.

4. **Crear (o localizar) el proyecto RELECOV**  
   - Si no existe, pulsa **Add** y crea un proyecto que incluya **“RELECOV”** en el nombre.  
   - En **Manager**, selecciona a **isabel.cuesta** (o el manager definido para tu instalación).  
   - Guarda los cambios.

5. **Cargar campos desde el schema (“Load batch”)**  
   - Dentro del proyecto RELECOV: **Define fields → Load batch**  
   - **Upload schema**: seleccionar el fichero `relecov_schema.json`.  
   - **Property where to fetch fields**: `classification`  
   - **Select the values to be filtered** (deben coincidir con las *Classification* del schema que quieras cargar). Marca:
     - Database Identifiers
     - Files info
     - Host information
     - Pathogen diagnostic testing
     - Sample collection and processing
     - Sequencing  
   - Confirma y guarda.

6. **Ontologymap (mapeo de variables)**  
   Configurar las relaciones entre las variables de iSkyLIMS para que mapear en base a la ontología del schema. Ir a:  
   `http://…./admin/core/ontologymap/` y ajustar, por ejemplo:
   - `sample_type` → `SNOMED:703065002`
   - `lab_request` → `GENEPIO:0001159` (submitting_institution)
   - `species` → `SNOMED:410607006` (Organism)
   - `sample_name` → `GENEPIO:0000079` (sequencing_sample_id)
   - `sample_entry_date` → `SNOMED:281271004` (received_date)
   - `collection_sample_date` → `SNOMED:399445004` (sample_collection_date)

7. **Definir *Species***  
   Dar de alta los distintos organismos del schema en `http://…./admin/core/species/`:
   - *Severe acute respiratory syndrome coronavirus 2*
   - *Respiratory syncytial virus*
   - *Influenza virus*

8. **Aplicar “wetlab”**  
   En el apartado de **Apps name** seleccionar **wetlab**.


## 7.3 Servicios iSkyLIMS (SAMBA, correo, Apache y verificación)

- **Servicios Iskylims (Realiza la configuración siguiendo **exclusivamente** el LEAME oficial)**  
  • [Configuración de SAMBA](https://github.com/BU-ISCIII/iskylims/blob/main/LEAME.md#configuración-de-samba)  
  • [Verificación de correo electrónico](https://github.com/BU-ISCIII/iskylims/blob/main/LEAME.md#verificación-de-correo-electrónico)  
  • [Configurar el servidor Apache](https://github.com/BU-ISCIII/iskylims/blob/main/LEAME.md#configurar-el-servidor-apache)  
  • [Verificación de la instalación](https://github.com/BU-ISCIII/iskylims/blob/main/LEAME.md#verificación-de-la-instalación)

---