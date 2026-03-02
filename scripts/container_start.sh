#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/relecov-platform"
CRON_DIR="${APP_DIR}/cron"
TMP_DIR="${APP_DIR}/tmp"
CRON_FILE="${CRON_DIR}/relecov-platform"
APP_MODE="${APP_MODE:-prod}"
APP_PORT="${APP_PORT:-8000}"
PROJECT_MODULE="${PROJECT_MODULE:-relecov_platform}"

while [ ! -f "${APP_DIR}/manage.py" ]; do
    sleep 2
done

source "${APP_DIR}/virtualenv/bin/activate"

mkdir -p "${CRON_DIR}" "${TMP_DIR}"
chmod 700 "${CRON_DIR}" "${TMP_DIR}"

if [ "$APP_MODE" = "dev" ]; then
    exec python "${APP_DIR}/manage.py" runserver "0.0.0.0:${APP_PORT}"
fi

if command -v crond >/dev/null 2>&1; then
    python "${APP_DIR}/manage.py" crontab show > "${CRON_FILE}" || true
    if [ -s "${CRON_FILE}" ]; then
        chmod 600 "${CRON_FILE}"
        crond -n -m off -c "${CRON_DIR}" -p "${TMP_DIR}/crond.pid" &
    else
        echo "No cron entries found. Skipping crond start."
    fi
else
    echo "crond not found. Skipping cron."
fi

exec gunicorn "${PROJECT_MODULE}.wsgi:application" \
    --bind "0.0.0.0:${APP_PORT}" \
    --workers 3 \
    --threads 2 \
    --timeout 120
