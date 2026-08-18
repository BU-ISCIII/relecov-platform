# Actualizacion de RELECOV Platform con Podman rootless

Esta guia es la lista de ejecucion para instalar, actualizar y recuperar el
despliegue de produccion. Los comandos generados son reutilizables. Antes de la
aprobacion, el responsable debe registrar las entradas de despliegue indicadas
abajo con valores o referencias institucionales verificadas.

## Indice

- [Requisitos](#requisitos)
- [Estructura de directorios en los servidores](#estructura-de-directorios-en-los-servidores)
- [Preparar checkout y backup](#preparar-checkout-y-backup)
- [Actualizar codigo](#actualizar-codigo)
- [Configurar los ajustes de produccion](#configurar-los-ajustes-de-produccion)
- [Preparar directorios persistentes del host](#preparar-directorios-persistentes-del-host)
- [Migrar datos en la primera instalacion de produccion](#migrar-datos-en-la-primera-instalacion-de-produccion)
- [Backup antes de actualizar](#backup-antes-de-actualizar)
- [Ejecutar la actualizacion](#ejecutar-la-actualizacion)
- [Comprobaciones posteriores](#comprobaciones-posteriores)
- [Rollback](#rollback)
- [Reparar permisos](#reparar-permisos)
- [Operaciones utiles](#operaciones-utiles)
- [Notas de permisos](#notas-de-permisos)

## Requisitos

- Podman rootless y un proveedor de Compose funcionales.
- El mismo usuario sin privilegios para el instalador y Podman.
Entradas de despliegue que deben quedar registradas antes de ejecutar:

| Entrada | Evidencia requerida |
|---|---|
| Revision aprobada | Tag o commit inmutable y aprobacion asociada |
| Exposicion publica | URL, DNS, propietario de TLS y reglas de proxy |
| Dependencias | Base de datos, almacenamiento, correo e identidad aplicables |
| Operacion | Responsable del servicio y contacto de escalado |
| Recuperacion | RPO, RTO, retencion y ubicacion de backups |

```bash
podman info
podman compose version || podman-compose --version
```

No ejecutar `container_install.sh` con `sudo`. Podman rootless, el proveedor de
Compose y el instalador deben usar siempre la misma cuenta. Los ejemplos usan
`podman compose`; si el host proporciona `podman-compose`, sustituir ese prefijo
completo. La libreria compartida detecta ambos proveedores automaticamente.

## Estructura de directorios en los servidores

Todos los despliegues usan esta estructura institucional. El nombre de la
aplicacion separa sus fuentes bind, logs y backups; Podman administra su propio
storage y no debe modificarse manualmente.

```text
/opt/containers_apps/
└── relecov-platform/
    ├── backup/                         # Backups locales opcionales
    └── relecov-platform/               # Clone Git y configuracion protegida

/srv/containers/
├── backup/
│   └── relecov-platform/               # Backup central recomendado
├── bind/
│   └── relecov-platform/
│       └── settings/                   # settings.py renderizado por servicio
├── shared/                             # Datos compartidos entre aplicaciones
└── storage/
    └── <usuario-podman>/               # Storage rootless gestionado por Podman

/var/log/local/
└── relecov-platform/
    ├── apache/
    └── apps/
```

Persistencia declarada por el despliegue:

| Activo | Ubicacion de produccion | Requisito de recuperacion |
|---|---|---|
| `app` database | External production database | Database backup before migration |
| `app` documents | `app_documents` named volume | Volume backup |
| `app` static | `app_static` named volume | Replaceable through collectstatic |
| `app` logs | Host bind configured by `HOST_LOG_PATH` in `app_production_settings.txt` | Retain/rotate per institutional log policy |
| `app` rendered settings | Host bind configured by `DJANGO_SETTINGS_PATH` in `app_production_settings.txt` | Protected configuration backup |
| `iskylims_app` database | External production database | Database backup before migration |
| `iskylims_app` documents | `iskylims_app_documents` named volume | Volume backup |
| `iskylims_app` static | `iskylims_app_static` named volume | Replaceable through collectstatic |
| `iskylims_app` logs | Host bind configured by `HOST_LOG_PATH` in `iskylims_app_production_settings.txt` | Retain/rotate per institutional log policy |
| `iskylims_app` rendered settings | Host bind configured by `DJANGO_SETTINGS_PATH` in `iskylims_app_production_settings.txt` | Protected configuration backup |
| Apache logs | `/var/log/local/relecov-platform/apache` host bind | Retain/rotate per institutional log policy |
| Rendered Apache configuration | `deployment/apache/` in the deployment checkout | Rebuildable; preserve reviewed source configuration |
| Nextstrain datasets | `nextstrain_data` named volume | Auspice/Nextstrain datasets served by `nextstrain view` |

## Preparar checkout y backup

Crear solo las ubicaciones necesarias para obtener el codigo y guardar backups.
Sustituir `<usuario-podman>` por la cuenta que ejecutara siempre Podman y el
instalador. Los binds y logs se crean despues de completar los ajustes.

```bash
sudo mkdir -p /opt/containers_apps/relecov-platform
sudo mkdir -p /srv/containers/backup/relecov-platform
sudo chown -R <usuario-podman>:<usuario-podman> \
  /opt/containers_apps/relecov-platform \
  /srv/containers/backup/relecov-platform
```

## Actualizar codigo

Para un checkout nuevo:

```bash
cd /opt/containers_apps/relecov-platform
git clone https://github.com/BU-ISCIII/relecov-platform.git relecov-platform
cd relecov-platform
git checkout <revision-aprobada>
```

En un checkout existente, verificar primero que no haya cambios locales y
cambiar a la revision entregada mediante el procedimiento Git de la institucion.
Registrar el commit exacto con `git rev-parse HEAD`.

## Configurar los ajustes de produccion

Crear un fichero ignorado y con modo `0600` por servicio a partir de su
`conf/docker_production_settings.txt`. Resolver todos los `CHANGE_ME` y revisar
la matriz [`conf/INSTALL_SETTINGS.md`](conf/INSTALL_SETTINGS.md). El instalador
genera `.env.production.file` con valores runtime, incluidos secretos copiados
desde estos ficheros protegidos. Mantenerlo con modo `0600`, fuera de Git y
dentro del backup protegido de configuracion. Ninguno de estos ficheros se
copia en las capas de las imagenes.

```bash
install -d -m 0700 deployment/settings
install -m 0600 conf/docker_production_settings.txt deployment/settings/app_production_settings.txt
install -m 0600 ../relecov-iskylims/conf/docker_production_settings.txt deployment/settings/iskylims_app_production_settings.txt
install -m 0600 conf/apache/apache_production_settings.txt deployment/settings/apache_production_settings.txt
install -m 0600 conf/nextstrain/nextstrain_production_settings.txt deployment/settings/nextstrain_production_settings.txt
```

Editar unicamente las copias bajo `deployment/settings/`. Los comandos de
instalacion y actualizacion usan estas rutas protegidas.

Valores que requieren decision del responsable de la aplicacion:

- hostnames publicos, TLS y proxy;
- base de datos y credenciales de minimo privilegio;
- rutas persistentes, UID/GID, SELinux y politica de backup;
- correo, identidad, almacenamiento y ajustes propios de la aplicacion;
- administrador inicial y transferencia segura de sus credenciales.

Completar todas esas decisiones y resolver cada `CHANGE_ME` antes de continuar.

## Preparar directorios persistentes del host

Solo despues de completar y revisar esos ficheros, crear los binds exactamente
donde indica cada servicio. Esto incluye el namespace independiente de iSkyLIMS:

```bash
PODMAN_USER='<usuario-podman>'
(
  source deployment/settings/app_production_settings.txt
  : "${HOST_LOG_PATH:?HOST_LOG_PATH is required for app}"
  : "${DJANGO_SETTINGS_PATH:?DJANGO_SETTINGS_PATH is required for app}"
  sudo install -d -o "$PODMAN_USER" -g "$PODMAN_USER" \
    "$HOST_LOG_PATH" "$(dirname "$DJANGO_SETTINGS_PATH")"
)
(
  source deployment/settings/iskylims_app_production_settings.txt
  : "${HOST_LOG_PATH:?HOST_LOG_PATH is required for iskylims_app}"
  : "${DJANGO_SETTINGS_PATH:?DJANGO_SETTINGS_PATH is required for iskylims_app}"
  sudo install -d -o "$PODMAN_USER" -g "$PODMAN_USER" \
    "$HOST_LOG_PATH" "$(dirname "$DJANGO_SETTINGS_PATH")"
)
(
  source deployment/settings/apache_production_settings.txt
  : "${APACHE_LOG_PATH:?APACHE_LOG_PATH is required for apache}"
  sudo install -d -o "$PODMAN_USER" -g "$PODMAN_USER" "$APACHE_LOG_PATH"
)
```

Los ficheros se cargan como el usuario actual dentro de subshells; solo
`install -d` usa privilegios. No ejecutar los ficheros completos con `sudo`.

Con los directorios preparados, aplicar UID/GID internos, modos y etiquetas
SELinux mediante el instalador. No modificar `/srv/containers/storage/`
manualmente.

```bash
bash container_install.sh --action fix-permissions --engine podman \
  --install_conf_map app,deployment/settings/app_production_settings.txt --install_conf_map iskylims_app,deployment/settings/iskylims_app_production_settings.txt --install_conf_map apache,deployment/settings/apache_production_settings.txt --install_conf_map nextstrain,deployment/settings/nextstrain_production_settings.txt
```

## Migrar datos en la primera instalacion de produccion

Esta seccion solo se aplica cuando la primera instalacion debe conservar las
bases de datos y documentos de un despliegue anterior. Preparar, como minimo,
los siguientes artefactos y comprobar sus sumas antes de comenzar:

```text
input/
|-- relecov_platform.sql
|-- relecov_iskylims.sql
|-- relecov_platform_documents.tar
|-- relecov_iskylims_documents.tar
`-- nextstrain_data.tar
```

Detener las escrituras en el sistema de origen antes de generar los dumps y
archives definitivos. Conservar una copia independiente hasta completar las
comprobaciones posteriores a la instalacion.

### Importar las bases de datos

Los nombres de base de datos, hosts y usuarios deben coincidir exactamente con
los ficheros protegidos de `deployment/settings/`. Crear las bases de datos y
conceder permisos con una cuenta administrativa; introducir las contrasenas de
forma interactiva para no guardarlas en el historial:

```bash
DB_HOST='<host-mysql>'
DB_PORT='3306'
PLATFORM_DB='<base-relecov-platform>'
ISKYLIMS_DB='<base-relecov-iskylims>'
APP_DB_USER='<usuario-django>'

mysql --host="$DB_HOST" --port="$DB_PORT" --user=root --password <<SQL
CREATE DATABASE IF NOT EXISTS \`${PLATFORM_DB}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS \`${ISKYLIMS_DB}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON \`${PLATFORM_DB}\`.* TO '${APP_DB_USER}'@'%';
GRANT ALL PRIVILEGES ON \`${ISKYLIMS_DB}\`.* TO '${APP_DB_USER}'@'%';
FLUSH PRIVILEGES;
SQL

mysql --host="$DB_HOST" --port="$DB_PORT" --user="$APP_DB_USER" --password \
  "$PLATFORM_DB" < input/relecov_platform.sql
mysql --host="$DB_HOST" --port="$DB_PORT" --user="$APP_DB_USER" --password \
  "$ISKYLIMS_DB" < input/relecov_iskylims.sql
```

### Restaurar documentos y datos de Nextstrain

Compose antepone normalmente el nombre del proyecto a los volumenes logicos,
pero el prefijo puede variar segun el directorio, `COMPOSE_PROJECT_NAME` y el
proveedor de Compose. Fijar y exportar un nombre estable antes de ejecutar el
instalador, crear explicitamente los tres volumenes y mantener esa variable en
la sesion usada para la instalacion:

```bash
export COMPOSE_PROJECT_NAME='relecov-platform'

podman volume create "${COMPOSE_PROJECT_NAME}_app_documents"
podman volume create "${COMPOSE_PROJECT_NAME}_iskylims_app_documents"
podman volume create "${COMPOSE_PROJECT_NAME}_nextstrain_data"

podman volume ls --format '{{.Name}}' | grep -E \
  '(^|_)(app_documents|iskylims_app_documents|nextstrain_data)$'
```

No asumir que esos son los nombres correctos si los volumenes ya existian o se
uso anteriormente otro nombre de proyecto. Identificar y revisar los tres
nombres fisicos antes de importar:

```bash
PLATFORM_DOCUMENTS_VOLUME='<nombre-real_app_documents>'
ISKYLIMS_DOCUMENTS_VOLUME='<nombre-real_iskylims_app_documents>'
NEXTSTRAIN_VOLUME='<nombre-real_nextstrain_data>'

podman volume inspect "$PLATFORM_DOCUMENTS_VOLUME"
podman volume inspect "$ISKYLIMS_DOCUMENTS_VOLUME"
podman volume inspect "$NEXTSTRAIN_VOLUME"
```

Los volumenes de destino deben estar vacios. Cada `.tar` debe contener
directamente los ficheros que deben quedar en la raiz del volumen, no una
carpeta contenedora adicional llamada `documents` o `nextstrain_data`:

```text
relecov_platform_documents.tar
|-- <fichero_o_directorio_1>
`-- <fichero_o_directorio_2>
```

Comprobar la estructura y efectuar la importacion:

```bash
tar -tf input/relecov_platform_documents.tar | head
tar -tf input/relecov_iskylims_documents.tar | head
tar -tf input/nextstrain_data.tar | head

podman volume import "$PLATFORM_DOCUMENTS_VOLUME" \
  input/relecov_platform_documents.tar
podman volume import "$ISKYLIMS_DOCUMENTS_VOLUME" \
  input/relecov_iskylims_documents.tar
podman volume import "$NEXTSTRAIN_VOLUME" input/nextstrain_data.tar
```

Ejecutar despues la primera instalacion con `container_install.sh` desde la
misma sesion, conservando `COMPOSE_PROJECT_NAME`. El instalador debe reutilizar
estos volumenes, aplicar permisos, ejecutar las migraciones pendientes y
conservar los datos importados. Verificar al terminar que ambas aplicaciones
muestran sus documentos y que Nextstrain publica todos los datasets esperados.

## Backup antes de actualizar

Crear un directorio identificado y registrar el estado desplegado:

```bash
BACKUP_DIR="/srv/containers/backup/relecov-platform/$(date +%Y%m%d_%H%M%S)"
sudo mkdir -p "$BACKUP_DIR"
git rev-parse HEAD > "$BACKUP_DIR/git-revision.txt"
podman compose --env-file .env.production.file -f docker-compose.prod.yml \
  images > "$BACKUP_DIR/images.txt"
cp .env.production.file "$BACKUP_DIR/"
cp deployment/settings/app_production_settings.txt "$BACKUP_DIR/"
cp deployment/settings/iskylims_app_production_settings.txt "$BACKUP_DIR/"
cp deployment/settings/apache_production_settings.txt "$BACKUP_DIR/"
cp deployment/settings/nextstrain_production_settings.txt "$BACKUP_DIR/"
cp deployment/settings/samba_production_settings.txt "$BACKUP_DIR/"
chmod -R go-rwx "$BACKUP_DIR"
```

Exportar la base de datos externa desde un punto coherente:

```bash
mysqldump --single-transaction --routines --triggers \
  --host=<db-host> --port=<db-port> --user=<db-user> --password \
  <db-name> > "$BACKUP_DIR/database.sql"
```

Localizar y exportar cada volumen no reconstruible declarado en la tabla:

```bash
podman volume ls | grep 'relecov-platform'
podman volume export <volumen-documents> > "$BACKUP_DIR/documents.tar"
podman volume export <volumen-static> > "$BACKUP_DIR/static.tar"
podman volume export relecov-platform_nextstrain_data > "$BACKUP_DIR/nextstrain_data.tar"
```

Exportar `documents` y `static` por cada servicio Django que los declare;
omitir esos comandos para perfiles sin dichos volumenes. Aunque `static` puede
regenerarse con `collectstatic`, conservarlo permite una restauracion exacta.

Guardar tambien los bind mounts persistentes. Los logs se conservan segun su
politica de retencion; la configuracion protegida debe incluirse siempre.

```bash
tar -C /srv/containers/bind -czf "$BACKUP_DIR/bind-mounts.tar.gz" relecov-platform
tar -C /var/log/local -czf "$BACKUP_DIR/logs.tar.gz" relecov-platform
sha256sum "$BACKUP_DIR"/* > "$BACKUP_DIR/SHA256SUMS"
```

No continuar hasta verificar los ficheros, espacio disponible y procedimiento
de restauracion.

## Ejecutar la actualizacion

Primera instalacion:

```bash
bash container_install.sh --action install --engine podman \
  --git_revision <revision-aprobada> \
  --install_conf_map app,deployment/settings/app_production_settings.txt --install_conf_map iskylims_app,deployment/settings/iskylims_app_production_settings.txt --install_conf_map apache,deployment/settings/apache_production_settings.txt --install_conf_map nextstrain,deployment/settings/nextstrain_production_settings.txt
```

Actualizacion:

```bash
bash container_install.sh --action upgrade --engine podman \
  --git_revision <nueva-revision-aprobada> \
  --install_conf_map app,deployment/settings/app_production_settings.txt --install_conf_map iskylims_app,deployment/settings/iskylims_app_production_settings.txt --install_conf_map apache,deployment/settings/apache_production_settings.txt --install_conf_map nextstrain,deployment/settings/nextstrain_production_settings.txt
```

Durante `--action upgrade`, `container_install.sh`:

1. valida opciones, configuraciones protegidas y Compose antes de modificar el
   despliegue;
2. genera `.env.production.file` y las configuraciones runtime protegidas;
3. prepara bind mounts, propietarios, modos y etiquetas SELinux;
4. construye las imagenes desde la revision aprobada;
5. recrea la topologia conservando volumenes y bind mounts persistentes;
6. espera readiness y repara los volumenes desde los contenedores en ejecucion;
7. ejecuta el bootstrap requerido por cada perfil —checks, migraciones,
   scripts/fixtures y `collectstatic` para Django—;
8. ejecuta el smoke test y solo entonces declara completada la actualizacion.

Seguir ademas la guia especifica de la version cuando exista. Detenerse ante
cualquier fallo de build, readiness, bootstrap, migracion o smoke test.

## Comprobaciones posteriores

```bash
podman compose --env-file .env.production.file -f docker-compose.prod.yml ps
podman compose --env-file .env.production.file -f docker-compose.prod.yml logs --tail 200
bash scripts/smoke_test.sh --engine podman
```

Completar las comprobaciones que corresponden a la topologia seleccionada:

- `app` e `iskylims_app`: confirmar `/health/` y un flujo real de cada servicio.
- Apache: confirmar la URL publica, DNS/TLS, proxy y cabeceras reenviadas.
- Nextstrain: confirmar la ruta publica y todos los datasets o narrativas.
- Samba: en los modos habilitados, confirmar acceso autenticado y un flujo de
  lectura/escritura desde un cliente aprobado.

Verificar tambien correo y tareas programadas. Registrar URL y resultados junto
con estado, imagenes y revision desplegada.

## Rollback

Si el esquema y los formatos persistentes siguen siendo compatibles, desplegar
la revision anterior registrada y repetir las pruebas:

```bash
bash container_install.sh --action upgrade --engine podman \
  --git_revision <revision-anterior> \
  --install_conf_map app,deployment/settings/app_production_settings.txt --install_conf_map iskylims_app,deployment/settings/iskylims_app_production_settings.txt --install_conf_map apache,deployment/settings/apache_production_settings.txt --install_conf_map nextstrain,deployment/settings/nextstrain_production_settings.txt
```

Si no son compatibles, detener escrituras y restaurar el punto completo:

```bash
podman compose --env-file .env.production.file -f docker-compose.prod.yml down
mysql --host=<db-host> --port=<db-port> --user=<db-user> --password \
  <db-name> < "$BACKUP_DIR/database.sql"
podman volume import <volumen-documents> "$BACKUP_DIR/documents.tar"
podman volume import <volumen-static> "$BACKUP_DIR/static.tar"
tar -C /srv/containers/bind -xzf "$BACKUP_DIR/bind-mounts.tar.gz"
install -d -m 0700 deployment/settings
install -m 0600 "$BACKUP_DIR/app_production_settings.txt" deployment/settings/app_production_settings.txt
install -m 0600 "$BACKUP_DIR/iskylims_app_production_settings.txt" deployment/settings/iskylims_app_production_settings.txt
install -m 0600 "$BACKUP_DIR/apache_production_settings.txt" deployment/settings/apache_production_settings.txt
install -m 0600 "$BACKUP_DIR/nextstrain_production_settings.txt" deployment/settings/nextstrain_production_settings.txt
install -m 0600 "$BACKUP_DIR/samba_production_settings.txt" deployment/settings/samba_production_settings.txt
```

Restaurar el fichero de ajustes protegido, desplegar la revision anotada en
`git-revision.txt` y dejar que el instalador regenere `.env.production.file`.
Ejecutar `fix-permissions`, arrancar y validar antes de
reabrir el servicio. Los volumenes deben existir y estar vacios antes de
`podman volume import`; recrearlos con Compose cuando sea necesario.

## Reparar permisos

Ejecutar esta accion cuando:

- se hayan creado o restaurado bind mounts o volumenes;
- se hayan recreado contenedores manualmente;
- hayan cambiado `APP_UID`, `APP_GID` o el usuario rootless;
- existan errores de escritura en logs, documentos, static o configuracion;
- SELinux rechace un bind mount revisado;
- Apache o la aplicacion fallen por propietarios/modos incorrectos.

Primera fase, incluso con los contenedores detenidos:

```bash
bash container_install.sh --action fix-permissions --engine podman \
  --install_conf_map app,deployment/settings/app_production_settings.txt --install_conf_map iskylims_app,deployment/settings/iskylims_app_production_settings.txt --install_conf_map apache,deployment/settings/apache_production_settings.txt --install_conf_map nextstrain,deployment/settings/nextstrain_production_settings.txt
```

Esta accion no construye imagenes, no migra la base de datos y no borra datos.
Con los contenedores detenidos repara los bind mounts accesibles desde el host.
Arrancar y repetirla para reparar tambien los volumenes montados:

```bash
podman compose --env-file .env.production.file -f docker-compose.prod.yml up -d
bash container_install.sh --action fix-permissions --engine podman \
  --install_conf_map app,deployment/settings/app_production_settings.txt --install_conf_map iskylims_app,deployment/settings/iskylims_app_production_settings.txt --install_conf_map apache,deployment/settings/apache_production_settings.txt --install_conf_map nextstrain,deployment/settings/nextstrain_production_settings.txt
```

## Operaciones utiles

```bash
podman compose --env-file .env.production.file -f docker-compose.prod.yml ps
podman compose --env-file .env.production.file -f docker-compose.prod.yml logs --tail 200
podman compose --env-file .env.production.file -f docker-compose.prod.yml up -d
podman compose --env-file .env.production.file -f docker-compose.prod.yml restart
podman compose --env-file .env.production.file -f docker-compose.prod.yml down
```

### Servicio Django `app`

```bash
# Logs separados del servicio.
podman compose --env-file .env.production.file -f docker-compose.prod.yml \
  logs --tail 200 app

# Entrar al contenedor.
podman compose --env-file .env.production.file -f docker-compose.prod.yml \
  exec app bash

# Regenerar static sin ejecutar migraciones.
podman compose --env-file .env.production.file -f docker-compose.prod.yml \
  exec app bash -lc \
  'cd "$INSTALL_PATH" && source virtualenv/bin/activate && python manage.py collectstatic --noinput'

# Diagnostico previo a una recuperacion de bootstrap.
podman compose --env-file .env.production.file -f docker-compose.prod.yml \
  exec app bash -lc \
  'cd "$INSTALL_PATH" && source virtualenv/bin/activate && python manage.py check --deploy && python manage.py showmigrations --plan'
```

La recuperacion preferida es corregir la causa y repetir
`container_install.sh --action install|upgrade` con la misma revision y
configuracion protegida. Si el instalador no puede completarse y el responsable
autoriza un bootstrap manual despues del backup:

```bash
podman compose --env-file .env.production.file -f docker-compose.prod.yml \
  exec app bash -lc \
  'cd "$INSTALL_PATH" && source virtualenv/bin/activate && python manage.py migrate --noinput && python manage.py collectstatic --noinput'
```

Registrar este procedimiento excepcional y ejecutar despues el smoke test.

### Servicio Django `iskylims_app`

```bash
# Logs separados del servicio.
podman compose --env-file .env.production.file -f docker-compose.prod.yml \
  logs --tail 200 iskylims_app

# Entrar al contenedor.
podman compose --env-file .env.production.file -f docker-compose.prod.yml \
  exec iskylims_app bash

# Regenerar static sin ejecutar migraciones.
podman compose --env-file .env.production.file -f docker-compose.prod.yml \
  exec iskylims_app bash -lc \
  'cd "$INSTALL_PATH" && source virtualenv/bin/activate && python manage.py collectstatic --noinput'

# Diagnostico previo a una recuperacion de bootstrap.
podman compose --env-file .env.production.file -f docker-compose.prod.yml \
  exec iskylims_app bash -lc \
  'cd "$INSTALL_PATH" && source virtualenv/bin/activate && python manage.py check --deploy && python manage.py showmigrations --plan'
```

La recuperacion preferida es corregir la causa y repetir
`container_install.sh --action install|upgrade` con la misma revision y
configuracion protegida. Si el instalador no puede completarse y el responsable
autoriza un bootstrap manual despues del backup:

```bash
podman compose --env-file .env.production.file -f docker-compose.prod.yml \
  exec iskylims_app bash -lc \
  'cd "$INSTALL_PATH" && source virtualenv/bin/activate && python manage.py migrate --noinput && python manage.py collectstatic --noinput'
```

Registrar este procedimiento excepcional y ejecutar despues el smoke test.

### Servicio Apache

```bash
# Logs separados de Apache y validacion de configuracion.
podman compose --env-file .env.production.file -f docker-compose.prod.yml \
  logs --tail 200 apache
podman compose --env-file .env.production.file -f docker-compose.prod.yml \
  exec apache httpd -t

# Estado restringido; usar valores del fichero protegido.
APACHE_PORT='CHANGE_ME'
SERVER_STATUS_SERVER_NAME='localhost'
curl --fail --show-error \
  --header "Host: $SERVER_STATUS_SERVER_NAME" \
  "http://127.0.0.1:$APACHE_PORT/server-status?auto"
```

Para diagnosticos SELinux y ModSecurity, comprobar el bind de logs antes de
reiniciar:

```bash
ls -ldZ /var/log/local/relecov-platform/apache
```

Si aparece `ModSecurity: Failed to open debug log file`, conservar el fichero
para diagnostico, ejecutar `fix-permissions` y reiniciar. Si hay que sustituir
el inode, moverlo primero a un backup en vez de borrarlo.

### Cargar datos de Nextstrain

El instalador crea y conserva el volumen `nextstrain_data`, pero no selecciona
ni descarga datasets. Copiar los datos Auspice revisados mediante el servicio
en ejecucion para escribir en el volumen montado:

```bash
NEXTSTRAIN_SOURCE='/srv/relecov-nextstrain-data'
NEXTSTRAIN_DATA_DIR='/data' # Debe coincidir con la configuracion protegida.
test -d "$NEXTSTRAIN_SOURCE"
podman compose --env-file .env.production.file -f docker-compose.prod.yml \
  cp "$NEXTSTRAIN_SOURCE/." "nextstrain:$NEXTSTRAIN_DATA_DIR/"
podman compose --env-file .env.production.file -f docker-compose.prod.yml \
  exec nextstrain find "$NEXTSTRAIN_DATA_DIR" -maxdepth 2 -type f
```

Usar `docker` en lugar de `podman` cuando corresponda. La copia no elimina
datasets antiguos: realizar primero un backup y retirar ficheros obsoletos de
forma explicita. No borrar el volumen durante una actualizacion normal.

```bash
podman compose --env-file .env.production.file -f docker-compose.prod.yml \
  exec -T nextstrain tar -C /data -czf - . > nextstrain-data.tar.gz
```

Verificar finalmente la URL publica y todos los datasets o narrativas esperados.

## Notas de permisos

- Ejecutar siempre Podman y el instalador con el mismo usuario rootless.
- No usar `sudo container_install.sh` ni cambiar propietarios dentro del storage
  de Podman.
- Mantener estables los UID/GID de runtime entre actualizaciones.
- Revisar etiquetas SELinux y propietarios de bind mounts mediante
  `fix-permissions`.
- Preservar evidencias y backups antes de cualquier recuperacion destructiva.
