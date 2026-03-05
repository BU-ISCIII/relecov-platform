#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/relecov-platform"
CRON_DIR="${APP_DIR}/cron"
TMP_DIR="${APP_DIR}/tmp"
CRON_FILE="${CRON_DIR}/relecov-platform"
CRON_LOG="${TMP_DIR}/supercronic.log"
APP_MODE="${APP_MODE:-prod}"
APP_PORT="${APP_PORT:-8000}"
PROJECT_MODULE="${PROJECT_MODULE:-relecov_platform}"

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
chmod 700 "${CRON_DIR}" "${TMP_DIR}"

if [ "$APP_MODE" = "dev" ]; then
    exec python "${APP_DIR}/manage.py" runserver "0.0.0.0:${APP_PORT}"
fi

if command -v supercronic >/dev/null 2>&1; then
    # Ensure django-crontab definitions are installed in user crontab first.
    python "${APP_DIR}/manage.py" crontab add >/dev/null 2>&1 || true
    crontab -l 2>/dev/null | sed '/^\s*#/d; /^\s*$/d' > "${CRON_FILE}" || true
    if [ -s "${CRON_FILE}" ]; then
        chmod 600 "${CRON_FILE}"
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

exec gunicorn "${PROJECT_MODULE}.wsgi:application" \
    --bind "0.0.0.0:${APP_PORT}" \
    --workers 1 \
    --threads 1 \
    --timeout 120
