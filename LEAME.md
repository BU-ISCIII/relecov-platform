# Instalacion de RELECOV Platform en produccion con Podman rootless

Esta guia resume los comandos para desplegar en produccion la pila integrada:

- RELECOV Platform
- iSkyLIMS
- Nextstrain
- Apache reverse proxy en contenedor
- Base de datos MySQL/MariaDB externa

Se asume que los datos iniciales vienen del entorno de desarrollo:

- dump de base de datos de `relecov-platform`
- dump de base de datos de `relecov-iskylims`
- documentos de `relecov-platform`
- documentos de `relecov-iskylims`
- datos de Nextstrain

Los ejemplos usan Podman rootless. Si se usa Docker, sustituir `--engine podman` por `--engine docker` y `podman compose` por `docker compose`.

## Indice

- [Instalacion de RELECOV Platform en produccion con Podman rootless](#instalacion-de-relecov-platform-en-produccion-con-podman-rootless)
  - [Indice](#indice)
  - [Requisitos minimos del host](#requisitos-minimos-del-host)
  - [Clonar repositorios](#clonar-repositorios)
  - [Preparar directorios del host](#preparar-directorios-del-host)
  - [Preparar ficheros recibidos de desarrollo](#preparar-ficheros-recibidos-de-desarrollo)
  - [Crear bases de datos de produccion e importar dumps](#crear-bases-de-datos-de-produccion-e-importar-dumps)
  - [Crear volumenes e importar documentos y Nextstrain](#crear-volumenes-e-importar-documentos-y-nextstrain)
  - [Configurar produccion](#configurar-produccion)
  - [Instalar contenedores](#instalar-contenedores)
  - [Reparar permisos](#reparar-permisos)
  - [Comprobaciones](#comprobaciones)
  - [Operaciones utiles](#operaciones-utiles)

## Requisitos minimos del host

- `git`
- Podman rootless y `podman-compose` o `podman compose`
- Docker Engine y Docker Compose v2 si no se usa Podman
- Acceso a un servidor MySQL/MariaDB de produccion
- Cliente MySQL/MariaDB en el host para crear bases de datos e importar dumps
- Usuario de sistema con permisos para ejecutar contenedores rootless
- Permisos de `sudo` solo para preparar paquetes y directorios del host

No ejecutar `container_install.sh` con `sudo`. El usuario que ejecuta Podman debe ser el mismo usuario que ejecuta el instalador.

## Clonar repositorios

Los dos repositorios deben quedar al mismo nivel:

```bash
mkdir -p /opt/containers_apps/relecov-platform-all
cd /opt/containers_apps/relecov-platform-all

git clone https://github.com/BU-ISCIII/relecov-platform.git relecov-platform
git clone https://github.com/BU-ISCIII/iskylims.git relecov-iskylims
```

Actualizar codigo si los repositorios ya existen:

```bash
cd /opt/containers_apps/relecov-platform-all/relecov-platform
git pull

cd /opt/containers_apps/relecov-platform-all/relecov-iskylims
git pull
```

## Preparar directorios del host

Crear rutas de bind mounts para configuracion Apache y logs:

```bash
sudo mkdir -p /srv/containers/bind/relecov-platform/relecov_apache_conf
sudo mkdir -p /srv/containers/bind/relecov-platform/relecov_django_setting
sudo mkdir -p /var/log/local/relecov-platform/apache
sudo mkdir -p /var/log/local/relecov-platform/apps
sudo mkdir -p /var/log/local/relecov-iskylims/apps

sudo chown -R "_USER-RUNNING_PODMAN_:_USER-RUNNING_PODMAN_" /srv/containers/bind/relecov-platform/relecov_apache_conf
sudo chown -R "_USER-RUNNING_PODMAN_:_USER-RUNNING_PODMAN_" /srv/containers/bind/relecov-platform/relecov_django_setting
sudo chown -R "_USER-RUNNING_PODMAN_:_USER-RUNNING_PODMAN_" /var/log/local/relecov-platform
sudo chown -R "_USER-RUNNING_PODMAN_:_USER-RUNNING_PODMAN_" /var/log/local/relecov-platform
sudo chown -R "_USER-RUNNING_PODMAN_:_USER-RUNNING_PODMAN_" /var/log/local/relecov-iskylims

sudo chown -R "bioinfo:bioinfo" /srv/containers/bind/relecov-platform/relecov_apache_conf
sudo chown -R "bioinfo:bioinfo" /srv/containers/bind/relecov-platform/relecov_django_setting
sudo chown -R "bioinfo:bioinfo" /var/log/local/relecov-platform
sudo chown -R "bioinfo:bioinfo" /var/log/local/relecov-platform
sudo chown -R "bioinfo:bioinfo" /var/log/local/relecov-iskylims
```

Si la infraestructura usa rutas distintas, reflejarlas despues en `APACHE_CONF_PATH`, `APACHE_LOG_PATH`, `PLATFORM_LOG_PATH` e `ISKYLIMS_LOG_PATH`.

## Preparar ficheros recibidos de desarrollo

Ejemplo de carpeta de entrada:

```bash
mkdir -p /opt/containers_apps/relecov-platform-all/input
```

Copiar ahi estos ficheros, ajustando nombres si hace falta:

```text
/opt/containers_apps/relecov-platform-all/input/relecov_platform_dev.sql
/opt/containers_apps/relecov-platform-all/input/relecov_iskylims_dev.sql
/opt/containers_apps/relecov-platform-all/input/relecov_platform_documents.tar
/opt/containers_apps/relecov-platform-all/input/relecov_iskylims_documents.tar
/opt/containers_apps/relecov-platform-all/input/nextstrain_data.tar
```

## Crear bases de datos de produccion e importar dumps

Variables usadas en los comandos:

```bash
DB_HOST="<host_mysql>"
DB_PORT="3306"
DB_ADMIN_USER="root"

PLATFORM_DB="relecov_prod"
ISKYLIMS_DB="iskylims_prod"
APP_DB_USER="django"
APP_DB_PASS="<password_segura>"
```

Crear bases de datos y usuario:

```bash
mysql --user="$DB_ADMIN_USER" --password --host="$DB_HOST" --port="$DB_PORT" <<SQL
CREATE DATABASE IF NOT EXISTS ${PLATFORM_DB} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS ${ISKYLIMS_DB} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${APP_DB_USER}'@'%' IDENTIFIED BY '${APP_DB_PASS}';
GRANT ALL PRIVILEGES ON ${PLATFORM_DB}.* TO '${APP_DB_USER}'@'%';
GRANT ALL PRIVILEGES ON ${ISKYLIMS_DB}.* TO '${APP_DB_USER}'@'%';
FLUSH PRIVILEGES;
SQL
```

Importar dumps de desarrollo:

```bash
mysql --user="$APP_DB_USER" --password --host="$DB_HOST" --port="$DB_PORT" "$PLATFORM_DB" \
  < /opt/containers_apps/relecov-platform-all/input/relecov_platform_dev.sql

mysql --user="$APP_DB_USER" --password --host="$DB_HOST" --port="$DB_PORT" "$ISKYLIMS_DB" \
  < /opt/containers_apps/relecov-platform-all/input/relecov_iskylims_dev.sql
```

## Crear volumenes e importar documentos y Nextstrain

Usar un nombre de proyecto Compose estable para que los volumenes tengan nombres previsibles:

```bash
export COMPOSE_PROJECT_NAME=relecov
```

Crear volumenes:

```bash
podman volume create relecov_relecov_documents
podman volume create relecov_iskylims_documents
podman volume create relecov_nextstrain_data
```

Importar documentos y datos. `podman volume import` espera un fichero `.tar` con el contenido del volumen.

El `.tar` debe contener directamente lo que debe quedar dentro del volumen, no una carpeta contenedora adicional llamada `documents` o `nextstrain_data`.

Estructura esperada para `relecov_platform_documents.tar`:

```text
relecov_platform_documents.tar
|-- <fichero_o_directorio_1>
|-- <fichero_o_directorio_2>
`-- ...
```

Despues del import, debe quedar asi dentro del volumen:

```text
/opt/relecov-platform/documents/
|-- <fichero_o_directorio_1>
|-- <fichero_o_directorio_2>
`-- ...
```

No debe quedar asi:

```text
/opt/relecov-platform/documents/
`-- documents/
    |-- <fichero_o_directorio_1>
    `-- ...
```

Ejemplo para crear el `.tar` correctamente desde el entorno origen:

```bash
tar -cf relecov_platform_documents.tar -C /opt/relecov-platform/documents .
tar -cf relecov_iskylims_documents.tar -C /opt/iskylims/documents .
tar -cf nextstrain_data.tar -C /ruta/nextstrain_data .
```

Importar los `.tar`:

```bash
podman volume import relecov_relecov_documents /opt/containers_apps/relecov-platform-all/input/relecov_platform_documents.tar
podman volume import relecov_iskylims_documents /opt/containers_apps/relecov-platform-all/input/relecov_iskylims_documents.tar
podman volume import relecov_nextstrain_data /opt/containers_apps/relecov-platform-all/input/nextstrain_data.tar
```

Si el compose se ejecuto sin `COMPOSE_PROJECT_NAME=relecov`, revisar los nombres reales:

```bash
podman volume ls
```

## Configurar produccion

Crear ficheros de configuracion:

```bash
cd /opt/containers_apps/relecov-platform-all/relecov-platform

cp conf/docker_production_settings.txt conf/my_prod_settings_relecov.txt
cp ../relecov-iskylims/conf/docker_production_settings.txt ../relecov-iskylims/conf/my_prod_settings_iskylims.txt
```

Editar configuracion de RELECOV Platform:

```bash
nano conf/my_prod_settings_relecov.txt
```

Valores principales:

```bash
INSTALL_PATH='/opt/relecov-platform'
APACHE_CONF_PATH='/srv/containers/bind/relecov-platform/relecov_apache_conf'
DJANGO_SETTINGS_PATH='/srv/containers/bind/relecov-platform/relecov_django_setting/settings.py'
APACHE_LOG_PATH='/var/log/local/relecov-platform/apache'
PLATFORM_LOG_PATH='/var/log/local/relecov-platform/apps'
ISKYLIMS_LOG_PATH='/var/log/local/relecov-iskylims/apps'
APACHE_FORWARDED_PROTO='https'
APACHE_FORWARDED_PORT='443'
APACHE_HOST_PORT='8090'

APP_UID='1212'
APP_GID='1212'
APP_PORT='8000'
ISKYLIMS_APP_PORT='8001'
NEXTSTRAIN_PORT='8100'

DB_USER='django'
DB_PASS='<password_segura>'
DB_NAME='relecov_prod'
DB_SERVER_IP='<host_mysql>'
DB_PORT=3306

DNS_URL='relecov-platform.isciiides.es'
RELECOV_PLATFORM_SERVER_NAME='relecov-platform.isciiides.es'
RELECOV_ISKYLIMS_SERVER_NAME='relecov-iskylims.isciiides.es'
RELECOV_NEXTSTRAIN_SERVER_NAME='nextstrain.isciiides.es'

EMAIL_HOST_SERVER='<smtp>'
EMAIL_PORT='25'
EMAIL_HOST_USER='<correo>'
EMAIL_HOST_PASSWORD=''
EMAIL_USE_TLS='False'
```

Editar configuracion de iSkyLIMS:

```bash
nano ../relecov-iskylims/conf/my_prod_settings_iskylims.txt
```

Valores principales:

```bash
INSTALL_PATH='/opt/iskylims'
APP_UID='1212'
APP_GID='1212'
APP_PORT='8001'
APACHE_FORWARDED_PROTO='https'
APACHE_FORWARDED_PORT='443'

DB_USER='django'
DB_PASS='<password_segura>'
DB_NAME='iskylims_prod'
DB_SERVER_IP='<host_mysql>'
DB_PORT=3306

DNS_URL='relecov-iskylims.isciiides.es'

EMAIL_HOST_SERVER='<smtp>'
EMAIL_PORT='25'
EMAIL_HOST_USER='<correo>'
EMAIL_HOST_PASSWORD=''
EMAIL_USE_TLS='False'
```

## Instalar contenedores

Ejecutar desde `relecov-platform`:

```bash
cd /opt/containers_apps/relecov-platform/relecov-platform
export COMPOSE_PROJECT_NAME=relecov

bash container_install.sh --engine podman \
  --action upgrade \
  --git_revision develop \
  --install_conf_map app,my_prod_settings_relecov.txt \
  --install_conf_map iskylims_app,../relecov-iskylims/my_prod_settings_iskylims.txt \
  2>&1 | tee relecov_prod_install_$(date +%Y%m%d_%H%M%S).log
```

El instalador:

- construye las imagenes;
- genera `.env.prod.file`;
- renderiza la configuracion Apache;
- arranca `apache`, `app`, `iskylims_app` y `nextstrain`;
- aplica migraciones;
- refresca estaticos;
- prepara permisos de bind mounts y volumenes.

## Reparar permisos

Ejecutar si se han importado volumenes, cambiado propietarios, recreado contenedores manualmente o cambiado `APP_UID` / `APP_GID`:

```bash
cd /opt/containers_apps/relecov-platform-all/relecov-platform
export COMPOSE_PROJECT_NAME=relecov

bash container_install.sh --engine podman \
  --action fix-permissions \
  --install_conf_map app,my_prod_settings_relecov.txt \
  --install_conf_map iskylims_app,../relecov-iskylims/my_prod_settings_iskylims.txt
```

Si los contenedores no estaban arrancados, arrancar y repetir para reparar tambien los volumenes montados:

```bash
podman compose --env-file .env.prod.file -f docker-compose.prod.yml up -d

bash container_install.sh --engine podman \
  --action fix-permissions \
  --install_conf_map app,conf/my_prod_settings_relecov.txt \
  --install_conf_map iskylims_app,../relecov-iskylims/conf/my_prod_settings_iskylims.txt
```

## Comprobaciones

Estado de contenedores:

```bash
cd /opt/containers_apps/relecov-platform-all/relecov-platform
export COMPOSE_PROJECT_NAME=relecov

podman compose --env-file .env.prod.file -f docker-compose.prod.yml ps
```

Logs:

```bash
podman compose --env-file .env.prod.file -f docker-compose.prod.yml logs --tail 200 apache
podman compose --env-file .env.prod.file -f docker-compose.prod.yml logs --tail 200 app
podman compose --env-file .env.prod.file -f docker-compose.prod.yml logs --tail 200 iskylims_app
podman compose --env-file .env.prod.file -f docker-compose.prod.yml logs --tail 200 nextstrain
```

Checks Django:

```bash
podman exec -it relecov_app python /opt/relecov-platform/manage.py check
podman exec -it relecov_iskylims_app python /opt/iskylims/manage.py check
```

Checks por Apache:

```bash
curl -I -H "Host: relecov-platform.isciiides.es" http://<host>:8090
curl -I -H "Host: relecov-iskylims.isciiides.es" http://<host>:8090
curl -I -H "Host: nextstrain.isciiides.es" http://<host>:8090
```

## Operaciones utiles

Usar siempre `.env.prod.file` al ejecutar Compose directamente:

```bash
export COMPOSE_PROJECT_NAME=relecov

podman compose --env-file .env.prod.file -f docker-compose.prod.yml ps
podman compose --env-file .env.prod.file -f docker-compose.prod.yml up -d
podman compose --env-file .env.prod.file -f docker-compose.prod.yml restart app
podman compose --env-file .env.prod.file -f docker-compose.prod.yml restart iskylims_app
podman compose --env-file .env.prod.file -f docker-compose.prod.yml down
```

Entrar a contenedores:

```bash
podman exec -it relecov_app bash
podman exec -it relecov_iskylims_app bash
```

Exportar backups desde produccion:

```bash
BACKUP_DIR=~/relecov_prod_backup_$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

mysqldump --user="$APP_DB_USER" --password --host="$DB_HOST" --port="$DB_PORT" "$PLATFORM_DB" \
  > "$BACKUP_DIR/relecov_platform.sql"

mysqldump --user="$APP_DB_USER" --password --host="$DB_HOST" --port="$DB_PORT" "$ISKYLIMS_DB" \
  > "$BACKUP_DIR/relecov_iskylims.sql"

podman volume export relecov_relecov_documents > "$BACKUP_DIR/relecov_platform_documents.tar"
podman volume export relecov_iskylims_documents > "$BACKUP_DIR/relecov_iskylims_documents.tar"
podman volume export relecov_nextstrain_data > "$BACKUP_DIR/nextstrain_data.tar"
```
