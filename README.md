# RELECOV Platform

RELECOV Platform deployment guide (containers and bare-metal), including iSkyLIMS and Nextstrain integration.

- [RELECOV Platform](#relecov-platform)
  - [Get the code (required)](#get-the-code-required)
  - [Choose your path](#choose-your-path)
  - [Minimum requirements](#minimum-requirements)
  - [Docker deployment](#docker-deployment)
    - [Local test stack](#local-test-stack)
    - [Production container stack](#production-container-stack)
      - [Persist logs/documents on the host](#persist-logsdocuments-on-the-host)
      - [Apache reverse proxy (host)](#apache-reverse-proxy-host)
    - [Upgrade docker deployment](#upgrade-docker-deployment)
  - [Bare-metal deployment (Ubuntu/CentOS)](#bare-metal-deployment-ubuntucentos)
    - [Install](#install)
    - [Upgrade](#upgrade)
  - [Common operations (Docker + bare-metal)](#common-operations-docker--bare-metal)
    - [Database creation, users and grants](#database-creation-users-and-grants)
    - [Backups](#backups)
    - [Restore / rollback](#restore--rollback)
    - [What to do if something fails](#what-to-do-if-something-fails)
  - [Post-install configuration](#post-install-configuration)
    - [RELECOV Platform](#relecov-platform-1)
    - [iSkyLIMS](#iskylims)
    - [Smoke test](#smoke-test)
  - [Developer workflow](#developer-workflow)
    - [Migrations](#migrations)
    - [Container-based development loop](#container-based-development-loop)
    - [Persistent host paths](#persistent-host-paths)
    - [Useful diagnostics](#useful-diagnostics)

## Get the code (required)

```bash
git clone https://github.com/bu-isciii/relecov-platform.git
cd relecov-platform
```

iSkyLIMS is required for the integrated platform stack:

```bash
cd ..
git clone https://github.com/bu-isciii/relecov-iskylims.git
```

## Choose your path

- Docker (test): full local stack for validation.
- Docker (production): app + iSkyLIMS + Nextstrain containers pointing to your production DB.
- Bare-metal: install directly on the host using `install.sh`.

## Minimum requirements

Baseline software (minimum recommended):

- MySQL 8.0+ or MariaDB 10.4+
- Git 2.34+
- Python 3.11+
- Apache HTTP Server 2.4+ (for reverse proxy on production)
- Docker Engine + Compose v2, or Podman 4.9+ + `podman-compose`
- `tar`, `rsync`, `wget`, `curl`

Notes:

- This guide does not cover MySQL installation itself, only DB/user/grant creation and operational tasks.
- For container deployments with external DB, ensure network connectivity from containers to DB host/port.
- For Podman, prefer `host.containers.internal` in DB host settings.

## Docker deployment

Prerequisites:

- Docker Compose v2 or Podman + podman-compose.
- Both repositories checked out side-by-side:
  - `relecov-platform`
  - `relecov-iskylims`

### Local test stack

Runs:

- `relecov_test_db` (MySQL)
- `relecov_test_app` (RELECOV Platform)
- `relecov_test_iskylims_app` (iSkyLIMS)
- `relecov_test_nextstrain` (Nextstrain viewer)

Basic test install:

```bash
cd relecov-platform
bash container_install.sh --test --engine podman 2>&1 | tee relecov_test_install.log
```

Per-service conf mapping (recommended):

```bash
bash container_install.sh --test --engine podman \
  --install_conf_map app,conf/docker_test_platform_settings.txt \
  --install_conf_map iskylims_app,conf/docker_test_iskylims_settings.txt \
  2>&1 | tee relecov_test_install.log
```

### Production container stack

1. Prepare production confs (separate for each service):

```bash
cp conf/docker_production_settings.txt conf/docker_production_platform_settings.txt
cp ../relecov-iskylims/conf/docker_production_settings.txt ../relecov-iskylims/conf/docker_production_iskylims_settings.txt
```

2. Edit both files with your production DB/network values.

3. Deploy:

```bash
cd relecov-platform
bash container_install.sh --engine podman \
  --action install \
  --install_conf_map app,conf/docker_production_platform_settings.txt \
  --install_conf_map iskylims_app,../relecov-iskylims/conf/docker_production_iskylims_settings.txt \
  2>&1 | tee relecov_prod_install.log
```

4. Endpoints:

- RELECOV Platform: `http://<host>:8000`
- iSkyLIMS: `http://<host>:8001`
- Nextstrain: `http://<host>:8100`

#### Persist logs/documents on the host

For production container deployments, keep these paths persistent:

- Logs: `/var/log/local/apps/relecov-platform` -> `/opt/relecov-platform/logs`
- Documents: named volume `relecov_documents` -> `/opt/relecov-platform/documents`
- Static: `/opt/relecov-platform/static-host` -> `/opt/relecov-platform/static`

Prepare host directories and ownership:

```bash
sudo mkdir -p /var/log/local/apps/relecov-platform
sudo mkdir -p /opt/relecov-platform/static-host
sudo chown -R ${APP_UID:-1212}:${APP_GID:-1212} /var/log/local/apps/relecov-platform /opt/relecov-platform/static-host
```

#### Apache reverse proxy (host)

For production, host Apache can proxy the platform container on `localhost:8000`.

You can use the existing Apache templates in this repository:

- Ubuntu/Debian: `conf/relecov_apache_ubuntu.conf`
- CentOS/RHEL: `conf/relecov_apache_centos_redhat.conf`

Copy and enable (adapt paths/domain names to your environment):

```bash
# Ubuntu/Debian
sudo cp conf/relecov_apache_ubuntu.conf /etc/apache2/sites-available/relecov-platform.conf
sudo a2ensite relecov-platform.conf
sudo a2enmod proxy proxy_http headers rewrite
sudo systemctl reload apache2

# CentOS/RHEL
sudo cp conf/relecov_apache_centos_redhat.conf /etc/httpd/conf.d/relecov-platform.conf
sudo systemctl reload httpd
```

### Upgrade docker deployment

Use `upgrade` when DB schema/data already exist.
> IMPORTANT:Before upgrading, perform backups from [Backups](#backups).

```bash
cd relecov-platform
bash container_install.sh --engine podman \
  --action upgrade \
  --install_conf_map app,conf/docker_production_platform_settings.txt \
  --install_conf_map iskylims_app,../relecov-iskylims/conf/docker_production_iskylims_settings.txt \
  2>&1 | tee relecov_prod_upgrade.log
```

## Bare-metal deployment (Ubuntu/CentOS)

### Install

1. Prepare DB/users/grants from [Database creation, users and grants](#database-creation-users-and-grants).
2. Edit config files:

- `relecov-platform/conf/install_settings.txt`
- `relecov-iskylims/conf/install_settings.txt`

3. Install dependencies + app (needs root):

```bash
cd relecov-platform
bash install.sh --install full --conf conf/install_settings.txt

cd ../relecov-iskylims
bash install.sh --install full --conf conf/install_settings.txt
```

### Upgrade

```bash
cd relecov-platform
bash install.sh --upgrade app --conf conf/install_settings.txt

cd ../relecov-iskylims
bash install.sh --upgrade app --conf conf/install_settings.txt
```

Before upgrading, perform backups from [Backups](#backups).

## Common operations (Docker + bare-metal)

### Database creation, users and grants

Run as MySQL root:

```sql
CREATE DATABASE IF NOT EXISTS relecov_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS iskylims_rel_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'relecov'@'%' IDENTIFIED BY 'djangopass';
CREATE USER IF NOT EXISTS 'relecovlims'@'%' IDENTIFIED BY 'djangopass';

CREATE USER IF NOT EXISTS 'relecov'@'localhost' IDENTIFIED BY 'djangopass';
CREATE USER IF NOT EXISTS 'relecovlims'@'localhost' IDENTIFIED BY 'djangopass';

GRANT ALL PRIVILEGES ON relecov_dev.* TO 'relecov'@'%';
GRANT ALL PRIVILEGES ON relecov_dev.* TO 'relecov'@'localhost';

GRANT ALL PRIVILEGES ON iskylims_rel_dev.* TO 'relecovlims'@'%';
GRANT ALL PRIVILEGES ON iskylims_rel_dev.* TO 'relecovlims'@'localhost';

FLUSH PRIVILEGES;
```

Verification:

```sql
SHOW GRANTS FOR 'relecov'@'%';
SHOW GRANTS FOR 'relecovlims'@'%';
```

### Backups

Database dumps:

```bash
mysqldump -h <db_host> -P <db_port> -u relecov -p relecov_dev > relecov_dev_$(date +%Y%m%d_%H%M%S).sql
mysqldump -h <db_host> -P <db_port> -u relecovlims -p iskylims_rel_dev > iskylims_rel_dev_$(date +%Y%m%d_%H%M%S).sql
```

RELECOV logs (host bind path used by production compose):

```bash
tar -czf relecov_logs_$(date +%Y%m%d_%H%M%S).tgz -C /var/log/local/apps/relecov-platform .
```

Docker/Podman named volumes (documents + nextstrain datasets):

```bash
# podman (replace with docker if needed)
podman run --rm -v relecov_documents:/from -v "$PWD":/to alpine \
  tar -czf /to/relecov_documents_$(date +%Y%m%d_%H%M%S).tgz -C /from .

podman run --rm -v nextstrain_data:/from -v "$PWD":/to alpine \
  tar -czf /to/nextstrain_data_$(date +%Y%m%d_%H%M%S).tgz -C /from .
```

Suggested backup order before any risky change:

1. DB dumps.
2. Documents volume.
3. Nextstrain datasets volume.
4. Logs archive.

### Restore / rollback

Restore DB:

```bash
mysql -h <db_host> -P <db_port> -u relecov -p relecov_dev < relecov_dev_YYYYMMDD_HHMMSS.sql
mysql -h <db_host> -P <db_port> -u relecovlims -p iskylims_rel_dev < iskylims_rel_dev_YYYYMMDD_HHMMSS.sql
```

Restore volumes:

```bash
podman run --rm -v relecov_documents:/to -v "$PWD":/from alpine \
  sh -lc "cd /to && tar -xzf /from/relecov_documents_YYYYMMDD_HHMMSS.tgz"

podman run --rm -v nextstrain_data:/to -v "$PWD":/from alpine \
  sh -lc "cd /to && tar -xzf /from/nextstrain_data_YYYYMMDD_HHMMSS.tgz"
```

Restore logs archive:

```bash
sudo mkdir -p /var/log/local/apps/relecov-platform
sudo tar -xzf relecov_logs_YYYYMMDD_HHMMSS.tgz -C /var/log/local/apps/relecov-platform
```

### What to do if something fails

Quick checks:

```bash
podman ps -a
podman logs --tail 200 relecov_app
podman logs --tail 200 relecov_iskylims_app
podman logs --tail 200 relecov_nextstrain
```

If deployment is broken after migration or bad data load, rollback using [Restore / rollback](#restore--rollback).

## Post-install configuration

### RELECOV Platform

1. Create the admin/superuser if not already created.
2. Load RELECOV schema:
in `Configuration -> SchemaHandling`, upload the latest `relecov_schema.json`:
`https://raw.githubusercontent.com/BU-ISCIII/relecov-tools/main/relecov_tools/schema/relecov_schema.json`
3. Load annotation GFF:
in `Configuration -> Annotation`, upload:
`conf/NC_045512.2.gff`
4. iSkyLIMS endpoint verification:
in `/admin/core/configsetting/`, ensure `ISKYLIMS_SERVER` points to your iSkyLIMS service (for example `relecov-lims` in test, or your production hostname).

### iSkyLIMS

Pre-load RELECOV sample project data before normal usage:

```bash
cd /opt/iskylims
source virtualenv/bin/activate
python manage.py migrate --noinput
python manage.py loaddata /path/to/relecov_iskylims_projects.json
```

If you need to generate that fixture from an existing environment:

```bash
cd /opt/iskylims
source virtualenv/bin/activate
python manage.py dumpdata --indent 2 core.SampleProjects > ~/relecov_iskylims_test_data.json
```

Then configure RELECOV in iSkyLIMS:

1. Create `relecovbot` in `/admin/auth/user/` and assign required permissions/groups for your integration flows.
2. Go to WetLab (`/wetlab`) and open:
`PARAMETERS SETTINGS -> Define Sample projects`.
3. If the project does not exist, create one including `RELECOV` in the name and set the manager (for example `isabel.cuesta` in your environment).
4. In that RELECOV project:
`Define fields -> Load batch`, then set:
- `upload schema`: `relecov_schema.json`
- `Property where to fetch fields`: `classification`
- select classifications to import:
  - Database Identifiers
  - Files info
  - Host information
  - Pathogen diagnostic testing
  - Sample collection and processing
  - Sequencing
5. Configure ontology mapping in `/admin/core/ontologymap/`:
- `lab_request` -> `GENEPIO:0001153` (submitting_institution)
- `species` -> `GENEPIO:0001386` (Organism)
- `sample_name` -> `GENEPIO:0001123` (sequencing_sample_id)
- `sample_entry_date` -> `NCIT:C93644` (received_date)
- `collection_sample_date` -> `GENEPIO:0001174` (sample_collection_date)
6. Define species in:
`PARAMETERS SETTINGS -> Initial Settings -> Define new Specie`.
Add all enum values used by your schema for `Organism` (or the ontology-mapped equivalent), for example:
- Severe acute respiratory syndrome coronavirus 2
- Respiratory syncytial virus
- Influenza virus
7. Ensure `wetlab` app assignment is enabled for the related flow.

### Smoke test

Recommended endpoint checks:

```bash
curl -I http://<host>:8000
curl -I http://<host>:8001
curl -I http://<host>:8100
```

## Developer workflow

### Migrations

Create and review migrations locally, then commit migration files:

```bash
cd /opt/relecov-platform
source virtualenv/bin/activate

python manage.py makemigrations core dashboard
python manage.py migrate --noinput
python manage.py showmigrations core dashboard
```

Do not rely on runtime auto-generation of migrations in production.

### Container-based development loop

```bash
# bring stack down (keep volumes)
podman-compose -f docker-compose.test.yml down

# rebuild changed services
podman-compose -f docker-compose.test.yml build app iskylims_app

# start again
podman-compose -f docker-compose.test.yml up -d
```

### Persistent host paths

See [Persist logs/documents on the host](#persist-logsdocuments-on-the-host) in the production deployment section.

### Useful diagnostics

```bash
podman exec -it relecov_test_app python /opt/relecov-platform/manage.py check
podman exec -it relecov_test_iskylims_app python /opt/iskylims/manage.py check
podman volume ls | grep -E 'relecov|nextstrain'
```
