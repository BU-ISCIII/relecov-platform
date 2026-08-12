#!/usr/bin/env bash
set -euo pipefail

install_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$install_script_dir"
# shellcheck disable=SC1091
source "$install_script_dir/deployment/lib/container/common.sh"
# shellcheck disable=SC1091
source "$install_script_dir/deployment/lib/container/django.sh"

APP_VERSION="0.2.0"
ACTION="install"
OPERATION_SCOPE="full"
WORKFLOW="standard"
GIT_REVISION="current"
INSTALL_CONF="./install_settings.txt"
LOAD_TABLES="false"
SKIP_TABLES="false"
SKIP_APACHE_RESTART="false"
SCRIPT_BEFORE=()
SCRIPT_AFTER=()
RENDER_SETTINGS="auto"
SETTINGS_OUTPUT=""
INITIAL_GIT_REF=""

usage() {
    cat <<'EOF'
Install, stage, or bootstrap RELECOV Platform.

Usage: ./install.sh [options]

  --install full|dep|app       Install dependencies, application, or both.
  --upgrade full|dep|app       Upgrade dependencies, application, or both.
  --stage install|upgrade      Stage an immutable image; never touch the DB.
  --bootstrap install|upgrade  Bootstrap an already staged application.
  --git_revision <revision>    Branch, tag, commit, or current (default).
  --conf <path>                Normalized installation settings file.
  --render-settings            Render Django settings during staging.
  --settings-output <path>     Override the rendered settings destination.
  --tables                     Load conf/first_install_tables.json.
  --skip_tables                Never load the initial fixture.
  --script_before <name[,args]>  Repeatable pre-migrate django-extensions hook.
  --script_after <name[,args]>   Repeatable post-migrate hook.
  --script <name[,args]>       Alias for --script_after.
  --docker                     Deprecated alias for --skip_apache_restart.
  --skip_apache_restart        Do not restart a host Apache service.
  --help
  --version

Examples:
  ./install.sh --install full --conf conf/docker_test_settings.txt --tables
  ./install.sh --upgrade app --git_revision v2.0.0 --script_before prepare_v2
  ./install.sh --stage install --conf conf/docker_test_settings.txt --render-settings
  ./install.sh --bootstrap upgrade --conf /tmp/runtime_install_settings.txt
EOF
}

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
info() { printf 'INFO: %s\n' "$*"; }
command_required() { command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"; }

while (($#)); do
    case "$1" in
        --git_revision) GIT_REVISION="${2:-}"; shift 2 ;;
        --conf) INSTALL_CONF="${2:-}"; shift 2 ;;
        --render-settings) RENDER_SETTINGS="true"; shift ;;
        --settings-output) SETTINGS_OUTPUT="${2:-}"; shift 2 ;;
        --stage|--bootstrap)
            WORKFLOW="${1#--}"
            [[ "${2:-}" =~ ^(install|upgrade)$ ]] || die "$1 requires install or upgrade"
            ACTION="$2"; OPERATION_SCOPE="app"; shift 2
            ;;
        --install|--upgrade)
            ACTION="${1#--}"; WORKFLOW="standard"
            [[ "${2:-}" =~ ^(full|dep|app)$ ]] || die "$1 requires full, dep, or app"
            OPERATION_SCOPE="$2"; shift 2
            ;;
        --script_before) [[ -n "${2:-}" ]] || die "$1 requires a value"; SCRIPT_BEFORE+=("$2"); shift 2 ;;
        --script_after|--script) [[ -n "${2:-}" ]] || die "$1 requires a value"; SCRIPT_AFTER+=("$2"); shift 2 ;;
        --tables) LOAD_TABLES="true"; shift ;;
        --skip_tables) SKIP_TABLES="true"; LOAD_TABLES="false"; shift ;;
        --docker|--skip_apache_restart) SKIP_APACHE_RESTART="true"; shift ;;
        --help) usage; exit 0 ;;
        --version) echo "$APP_VERSION"; exit 0 ;;
        *) die "Unknown option: $1" ;;
    esac
done

[[ "$WORKFLOW" != "stage" || ${#SCRIPT_BEFORE[@]} -eq 0 && ${#SCRIPT_AFTER[@]} -eq 0 ]] \
    || die "Migration scripts cannot run during the stage workflow"
[[ -f "$INSTALL_CONF" ]] || die "Configuration not found: $INSTALL_CONF"
if [[ "$INSTALL_CONF" != /* ]]; then
    INSTALL_CONF="$(cd "$(dirname "$INSTALL_CONF")" && pwd)/$(basename "$INSTALL_CONF")"
fi
if [[ "$WORKFLOW" != "stage" ]] && grep -Eq "^[A-Z0-9_]+=.*CHANGE_ME" "$INSTALL_CONF"; then
    die "Configuration still contains CHANGE_ME values"
fi
# shellcheck disable=SC1090
source "$INSTALL_CONF"
: "${INSTALL_PATH:?INSTALL_PATH is required}"
: "${PROJECT_MODULE:?PROJECT_MODULE is required}"
[[ "$PROJECT_MODULE" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] \
    || die "PROJECT_MODULE must be a valid Python package name"
: "${PYTHON_BIN_PATH:?PYTHON_BIN_PATH is required}"
: "${DB_HOST:?DB_HOST is required}"
: "${DB_PORT:?DB_PORT is required}"
: "${DB_NAME:?DB_NAME is required}"
: "${DB_USER:?DB_USER is required}"
: "${DB_PASSWORD:?DB_PASSWORD is required}"
REQUIRED_MODULES="${REQUIRED_MODULES:-}"
MIGRATION_MODULES="${MIGRATION_MODULES:-}"

if [[ "$RENDER_SETTINGS" == "auto" ]]; then
    [[ "$WORKFLOW" == "standard" ]] && RENDER_SETTINGS="true" || RENDER_SETTINGS="false"
fi

remember_git_ref() {
    git -C "$install_script_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1 || return 0
    INITIAL_GIT_REF="$(git -C "$install_script_dir" symbolic-ref --quiet --short HEAD \
        || git -C "$install_script_dir" rev-parse HEAD)"
}

restore_git_ref() {
    [[ -n "$INITIAL_GIT_REF" ]] || return 0
    git -C "$install_script_dir" checkout --quiet "$INITIAL_GIT_REF" || \
        printf 'WARNING: could not restore git revision %s\n' "$INITIAL_GIT_REF" >&2
}

checkout_git_revision() {
    [[ "$GIT_REVISION" != "current" ]] || return 0
    [[ -n "$INITIAL_GIT_REF" ]] || die "Cannot select $GIT_REVISION: source has no Git metadata"
    git -C "$install_script_dir" rev-parse --verify "${GIT_REVISION}^{commit}" >/dev/null 2>&1 \
        || die "Git revision is not available locally: $GIT_REVISION"
    [[ -z "$(git -C "$install_script_dir" status --porcelain)" ]] \
        || die "Commit or stash local changes before selecting $GIT_REVISION"
    git -C "$install_script_dir" checkout --quiet "$GIT_REVISION"
}

check_python() {
    command_required "$PYTHON_BIN_PATH"
    "$PYTHON_BIN_PATH" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' \
        || die "Python 3.10 or newer is required"
}

check_required_modules() {
    local module
    [[ -f "$install_script_dir/conf/urls.py" ]] \
        || die "Django URL configuration is missing: conf/urls.py"
    grep -Fq 'deployment_health.urls' \
        "$install_script_dir/conf/urls.py" \
        || die "conf/urls.py must include deployment_health.urls for the /health/ endpoint"
    for module in $REQUIRED_MODULES; do
        [[ -e "$install_script_dir/$module" ]] || die "Required application module is missing: $module"
    done
}

check_database() {
    # Prefer the MySQL CLI when available; container images use mysqlclient's
    # MySQLdb module from the application virtual environment.
    if command -v mysql >/dev/null 2>&1; then
        MYSQL_PWD="$DB_PASSWORD" mysql --host="$DB_HOST" --port="$DB_PORT" \
            --user="$DB_USER" --database="$DB_NAME" --execute='SELECT 1' >/dev/null \
            || die "Unable to connect to database $DB_NAME at $DB_HOST:$DB_PORT"
        return
    fi
    "$INSTALL_PATH/virtualenv/bin/python" - "$DB_HOST" "$DB_PORT" "$DB_USER" "$DB_PASSWORD" "$DB_NAME" <<'PY'
import sys
import MySQLdb
connection = MySQLdb.connect(host=sys.argv[1], port=int(sys.argv[2]),
    user=sys.argv[3], passwd=sys.argv[4], db=sys.argv[5])
connection.close()
PY
}

# ============================================================================
# APPLICATION CUSTOMIZATION POINTS
#
# Keep generic lifecycle code outside this section. Each hook has a safe no-op
# default. Add project behavior here, document why it is required, and make it
# idempotent so a failed deployment can be retried safely.
# ============================================================================

install_application_system_packages() {
    # Keep the Dockerfile limited to tools needed to launch this installer.
    # Framework build headers and post-install user-management tools belong to
    # this lifecycle and are installed before virtualenv creation.
    [[ "${SKIP_SYSTEM_PACKAGES:-0}" != "1" ]] || return 0
    [[ $(id -u) -eq 0 ]] || return 0
    if [[ -f /etc/debian_version ]]; then
        apt-get update
        apt-get install -y --no-install-recommends \
            python3-dev \
            default-libmysqlclient-dev \
            apache2-dev \
            build-essential \
            passwd
    elif command -v microdnf >/dev/null 2>&1; then
        microdnf install -y \
            python3.11-devel \
            mariadb-connector-c-devel \
            httpd-devel \
            gcc \
            gcc-c++ \
            make \
            shadow-utils
        microdnf clean all
    elif command -v dnf >/dev/null 2>&1; then
        dnf install -y \
            python3.11-devel \
            mariadb-connector-c-devel \
            httpd-devel \
            gcc \
            gcc-c++ \
            make \
            shadow-utils
    else
        die "Unsupported package manager for system dependency installation"
    fi
}

prepare_application_directories() {
    # Argument: final INSTALL_PATH. Create application-specific persistent
    # directories here. Generic logs/documents/static/cron/tmp already exist.
    # mkdir -p is intentionally idempotent and preserves existing schemas and
    # all other persistent directory contents during install and upgrade.
    mkdir -p "$1/documents/schemas"
}

stage_application_custom_files() {
    # Arguments: source directory, final INSTALL_PATH, action (install|upgrade).
    # Copy application-owned files that intentionally need extra processing;
    # the standard already installs the Django URL and optional routing files.
    # RELECOV currently has no additional files outside the normal source sync.
    return 0
}

write_application_runtime_env() {
    # Argument: final INSTALL_PATH. Use this only when the application reads a
    # runtime .env in addition to Django settings. Never hard-code credentials.
    # Patho Core-style example:
    #   umask 077
    #   printf 'OIDC_ISSUER=%s\n' "${OIDC_ISSUER:?required}" > "$1/.env"
    #   for key in $(compgen -A variable KEYCLOAK_ | sort); do
    #       printf '%s=%s\n' "$key" "${!key}" >> "$1/.env"
    #   done
    :
}

validate_application_runtime() {
    # Called after DB connectivity and before migrations. Validate optional
    # identity-provider or feature configuration here.
    # Example: require KEYCLOAK_ISSUER only when legacy auth is disabled:
    #   [[ "${ENABLE_LEGACY_AUTH:-true}" == true || -n "${KEYCLOAK_ISSUER:-}" ]] ||
    #       die "KEYCLOAK_ISSUER is required when legacy auth is disabled"
    :
}

before_django_migrate() {
    # Arguments: action and space-separated MIGRATION_MODULES. This is for
    # application migration preparation, not the user-selected runscript hooks.
    local action="$1" migration_modules="$2" module

    echo "Validating Django migration plan for $action"
    for module in $migration_modules; do
        python manage.py showmigrations "$module" --plan >/dev/null \
            || die "Unable to inspect migrations for Django app: $module"
    done
    python manage.py migrate --plan --noinput >/dev/null \
        || die "Unable to calculate the Django migration plan"
}

after_django_migrate() {
    # Create the initial administrator only for an explicitly enabled fresh
    # runtime bootstrap. Retries leave an existing account unchanged.
    [[ "$WORKFLOW" == "bootstrap" && "$ACTION" == "install" ]] || return 0
    [[ "${CREATE_INITIAL_SUPERUSER:-false}" == "true" ]] || return 0
    : "${DJANGO_SUPERUSER_USERNAME:?DJANGO_SUPERUSER_USERNAME is required}"
    : "${DJANGO_SUPERUSER_PASSWORD:?DJANGO_SUPERUSER_PASSWORD is required}"

    DJANGO_SUPERUSER_USERNAME="$DJANGO_SUPERUSER_USERNAME" \
    DJANGO_SUPERUSER_EMAIL="${DJANGO_SUPERUSER_EMAIL:-}" \
    DJANGO_SUPERUSER_PASSWORD="$DJANGO_SUPERUSER_PASSWORD" \
        python manage.py shell <<'PY'
import os

from django.contrib.auth import get_user_model

user_model = get_user_model()
username = os.environ["DJANGO_SUPERUSER_USERNAME"]
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
password = os.environ["DJANGO_SUPERUSER_PASSWORD"]
lookup = {user_model.USERNAME_FIELD: username}
user, created = user_model._default_manager.get_or_create(**lookup)
if created:
    if hasattr(user, "email"):
        user.email = email
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()
    print(f"Created initial superuser: {username}")
else:
    print(f"Initial superuser already exists: {username}")
PY
}

set_application_permissions() {
    # Argument: final INSTALL_PATH. Container image staging and runtime mount
    # permissions are owned by the Dockerfile and container_install.sh.
    [[ "$WORKFLOW" == "standard" ]] || return 0

    local install_path="$1"
    local install_user="${SUDO_USER:-$(id -un)}"
    local apache_group="apache"
    local logs_path="$install_path/logs"

    [[ -f /etc/debian_version ]] && apache_group="www-data"
    getent group "$apache_group" >/dev/null 2>&1 \
        || die "Required Apache group does not exist: $apache_group"

    case "${LOG_TYPE:-regular_folder}" in
        regular_folder)
            [[ ! -L "$logs_path" ]] \
                || die "$logs_path is a symbolic link but LOG_TYPE=regular_folder"
            mkdir -p "$logs_path"
            ;;
        symbolic_link)
            [[ -n "${LOG_PATH:-}" ]] \
                || die "LOG_PATH is required when LOG_TYPE=symbolic_link"
            [[ -d "$LOG_PATH" ]] \
                || die "Configured log directory does not exist: $LOG_PATH"
            if [[ -L "$logs_path" ]]; then
                [[ "$(readlink -f "$logs_path")" == "$(readlink -f "$LOG_PATH")" ]] \
                    || die "$logs_path points to a different location than LOG_PATH"
            else
                if [[ -d "$logs_path" ]]; then
                    rmdir "$logs_path" 2>/dev/null \
                        || die "Refusing to replace non-empty log directory: $logs_path"
                elif [[ -e "$logs_path" ]]; then
                    die "Refusing to replace non-directory log path: $logs_path"
                fi
                ln -s "$LOG_PATH" "$logs_path"
            fi
            logs_path="$LOG_PATH"
            ;;
        *) die "Unsupported LOG_TYPE: $LOG_TYPE" ;;
    esac

    mkdir -p "$install_path/documents/schemas"
    if [[ $(id -u) -eq 0 ]]; then
        chown -R "$install_user:$apache_group" \
            "$install_path/documents" "$logs_path"
    else
        printf 'WARNING: ownership update requires root; leaving owner/group unchanged.\n' >&2
    fi
    chmod -R u+rwX,g+rwX,o-rwx "$install_path/documents" "$logs_path"
    chmod 0775 "$install_path/documents" "$install_path/documents/schemas" "$logs_path"
}

restart_application_server() {
    # Called only for a direct standard workflow unless restart was skipped.
    # Example: systemctl reload apache2  (or httpd on RHEL-family systems).
    :
}

# ========================= END APPLICATION CUSTOMIZATION =====================

stage_dependencies() {
    checkout_git_revision
    check_python
    check_required_modules
    install_application_system_packages
    mkdir -p "$INSTALL_PATH"
    [[ -d "$INSTALL_PATH/virtualenv" ]] \
        || "$PYTHON_BIN_PATH" -m venv "$INSTALL_PATH/virtualenv"
    # shellcheck disable=SC1091
    source "$INSTALL_PATH/virtualenv/bin/activate"
    python -m pip install --upgrade pip wheel
    [[ -f conf/requirements.txt ]] || die "Missing conf/requirements.txt"
    python -m pip install -r conf/requirements.txt
}

stage_application_files() {
    checkout_git_revision
    [[ -d "$INSTALL_PATH/virtualenv" ]] \
        || die "virtualenv not found at $INSTALL_PATH; install dependencies first"
    # The Django wrapper is deployment-generated and must never be inherited
    # from an ignored local source tree or a previous staged installation.
    rm -rf "$INSTALL_PATH/$PROJECT_MODULE"
    rm -f "$INSTALL_PATH/manage.py"
    rsync -rl --delete \
        --exclude .git --exclude .env --exclude /logs --exclude /documents \
        --exclude /static --exclude /cron --exclude /tmp --exclude /virtualenv \
        --exclude /manage.py --exclude "/$PROJECT_MODULE" \
        ./ "$INSTALL_PATH/"
    mkdir -p "$INSTALL_PATH/logs" "$INSTALL_PATH/documents" \
        "$INSTALL_PATH/static" "$INSTALL_PATH/cron" "$INSTALL_PATH/tmp"
    prepare_application_directories "$INSTALL_PATH"
    "$INSTALL_PATH/virtualenv/bin/python" -m django startproject \
        "$PROJECT_MODULE" "$INSTALL_PATH"
    install -m 0644 "$install_script_dir/conf/urls.py" \
        "$INSTALL_PATH/$PROJECT_MODULE/urls.py"
    if [[ -f "$install_script_dir/conf/routing.py" ]]; then
        install -m 0644 "$install_script_dir/conf/routing.py" \
            "$INSTALL_PATH/$PROJECT_MODULE/routing.py"
    fi
    stage_application_custom_files "$install_script_dir" "$INSTALL_PATH" "$ACTION"
    printf '%s\n' "$GIT_REVISION" > "$INSTALL_PATH/.deployed_revision"
    if [[ "$RENDER_SETTINGS" == "true" ]]; then
        local template="$install_script_dir/conf/template_settings.py"
        local output="${SETTINGS_OUTPUT:-$INSTALL_PATH/$PROJECT_MODULE/settings.py}"
        [[ -f "$template" ]] || die "Django settings template not found: $template"
        render_django_settings_file "$template" "$output" "$INSTALL_CONF"
    fi
    write_application_runtime_env "$INSTALL_PATH"
    set_application_permissions "$INSTALL_PATH"
}

run_hook() {
    local specification="$1" script_name="${1%%,*}"
    local -a args=(manage.py runscript "$script_name")
    [[ -n "$script_name" ]] || die "Empty migration script name"
    [[ "$specification" != *,* ]] || args+=(--script-args "${specification#*,}")
    python "${args[@]}"
}

bootstrap_application() {
    [[ -f "$INSTALL_PATH/manage.py" ]] || die "manage.py not found; run --stage first"
    [[ -x "$INSTALL_PATH/virtualenv/bin/python" ]] || die "virtualenv not found; run --stage first"
    cd "$INSTALL_PATH"
    # shellcheck disable=SC1091
    source virtualenv/bin/activate
    check_database
    validate_application_runtime
    python manage.py check --deploy
    local hook
    for hook in "${SCRIPT_BEFORE[@]}"; do run_hook "$hook"; done
    before_django_migrate "$ACTION" "$MIGRATION_MODULES"
    python manage.py migrate --noinput
    if [[ "$LOAD_TABLES" == "true" && "$SKIP_TABLES" == "false" ]]; then
        [[ -f conf/first_install_tables.json ]] \
            || die "Initial table fixture not found: conf/first_install_tables.json"
        python manage.py loaddata conf/first_install_tables.json
    fi
    for hook in "${SCRIPT_AFTER[@]}"; do run_hook "$hook"; done
    after_django_migrate "$ACTION"
    python manage.py collectstatic --noinput
    local migration_log
    migration_log="$(mktemp "${TMPDIR:-/tmp}/relecov-platform-migrations.XXXXXX.log")"
    if ! python manage.py showmigrations --plan > "$migration_log" 2>&1 \
        || grep -Fq '[ ]' "$migration_log"; then
        cat "$migration_log" >&2
        rm -f "$migration_log"
        die "Django migration verification failed"
    fi
    rm -f "$migration_log"
}

remember_git_ref
trap restore_git_ref EXIT

case "$WORKFLOW" in
    stage) stage_dependencies; stage_application_files ;;
    bootstrap) bootstrap_application ;;
    standard)
        if [[ "$OPERATION_SCOPE" == "full" || "$OPERATION_SCOPE" == "dep" ]]; then
            stage_dependencies
        fi
        if [[ "$OPERATION_SCOPE" == "full" || "$OPERATION_SCOPE" == "app" ]]; then
            stage_application_files
            bootstrap_application
        fi
        if [[ "$SKIP_APACHE_RESTART" == "false" ]]; then restart_application_server; fi
        ;;
    *) die "Invalid workflow: $WORKFLOW" ;;
esac

info "$WORKFLOW $ACTION completed for RELECOV Platform at $INSTALL_PATH"
