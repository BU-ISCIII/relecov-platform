#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_INSTALL_PATH:-/opt/relecov-platform}"
CRON_DIR="${APP_DIR}/cron"
TMP_DIR="${APP_DIR}/tmp"
CRON_FILE="${CRON_DIR}/relecov-platform"
CRON_LOG="${TMP_DIR}/supercronic.log"
APP_MODE="${APP_MODE:-prod}"
APP_PORT="${APP_PORT:-8000}"
PROJECT_MODULE="${PROJECT_MODULE:-relecov_platform}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-600}"
GUNICORN_KEEPALIVE="${GUNICORN_KEEPALIVE:-5}"
GUNICORN_THREADS="${GUNICORN_THREADS:-2}"

WAIT_TIMEOUT_SECONDS=100
wait_start="${SECONDS}"
while [ ! -f "${APP_DIR}/manage.py" ]; do
    if (( SECONDS - wait_start >= WAIT_TIMEOUT_SECONDS )); then
        echo "Timed out after ${WAIT_TIMEOUT_SECONDS}s waiting for ${APP_DIR}/manage.py" >&2
        exit 1
    fi
    sleep 2
done

source "${APP_DIR}/virtualenv/bin/activate"

mkdir -p "${CRON_DIR}" "${TMP_DIR}"

safe_chmod() {
    local mode="$1"
    shift
    local path
    for path in "$@"; do
        if [ ! -e "${path}" ]; then
            continue
        fi
        if [ -O "${path}" ]; then
            chmod "${mode}" "${path}"
        else
            echo "Skipping chmod ${mode} on ${path}: not owned by $(id -un)."
        fi
    done
}

safe_chmod 700 "${CRON_DIR}" "${TMP_DIR}"

if [ "$APP_MODE" = "dev" ]; then
    exec python "${APP_DIR}/manage.py" runserver "0.0.0.0:${APP_PORT}"
fi

if command -v supercronic >/dev/null 2>&1; then
    python - <<'PY' > "${CRON_FILE}"
import os
import shlex
import sys

import django

app_dir = os.environ.get("APP_INSTALL_PATH", "/opt/relecov-platform")
project_module = os.environ.get("PROJECT_MODULE", "relecov_platform")
sys.path.insert(0, app_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"{project_module}.settings")
django.setup()

from django.conf import settings

python_bin = os.path.join(app_dir, "virtualenv", "bin", "python")
manage_py = os.path.join(app_dir, "manage.py")

for job in getattr(settings, "CRONJOBS", []):
    schedule, dotted_path = job[:2]
    module_name, function_name = dotted_path.rsplit(".", 1)
    python_code = f"import {module_name} as _m; _m.{function_name}()"
    command = (
        f"cd {shlex.quote(app_dir)} && "
        f"{shlex.quote(python_bin)} {shlex.quote(manage_py)} "
        f"shell -c {shlex.quote(python_code)}"
    )
    print(f"{schedule} {command}")
PY
    if [ -s "${CRON_FILE}" ]; then
        safe_chmod 600 "${CRON_FILE}"
        : > "${CRON_LOG}"
        supercronic "${CRON_FILE}" > "${CRON_LOG}" 2>&1 &
        CRON_PID=$!
        sleep 1
        if ! kill -0 "${CRON_PID}" 2>/dev/null; then
            echo "supercronic failed to start. Check ${CRON_LOG} for details."
        fi
    else
        echo "No cron entries found. Skipping cron start."
    fi
else
    echo "supercronic not found. Skipping cron."
fi

if [ -n "${WEB_CONCURRENCY:-}" ]; then
    GUNICORN_WORKERS="${WEB_CONCURRENCY}"
else
    cpu_count="$(getconf _NPROCESSORS_ONLN 2>/dev/null || nproc 2>/dev/null || echo 1)"
    if [ "${cpu_count}" -le 2 ]; then
        GUNICORN_WORKERS=2
    else
        GUNICORN_WORKERS=4
    fi
fi

exec gunicorn "${PROJECT_MODULE}.wsgi:application" \
    --bind "0.0.0.0:${APP_PORT}" \
    --workers "${GUNICORN_WORKERS}" \
    --threads "${GUNICORN_THREADS}" \
    --keep-alive "${GUNICORN_KEEPALIVE}" \
    --timeout "${GUNICORN_TIMEOUT}" \
    --worker-tmp-dir /dev/shm
