#!/usr/bin/bash

RELECOVPLATFORM_VERSION="1.0.0"

usage() {
cat << EOF
This script installs and upgrades the iskylims app.

Usage : $0 [--demo_data] [--git_revision] [--compose_file] [--install_conf] [--action] [--script] [--script_before] [--script_after] [--engine] [--test]
    Optional input data:
    --demo_data         | Provide already downloaded demo data from Zenodo
    --git_revision      | Specify the Git revision to install (default: main, or 'current' to use copied local sources)
    --compose_file      | Compose file to use (overrides default)
    --install_conf      | Settings file consumed during container image build (mandatory for production)
    --install_conf_map  | Service-specific settings file: service,path (can be repeated)
    --action            | install (default) or upgrade, to control DB initialisation steps
    --script            | Run a Django migration script after migrations (can be repeated)
    --script_before     | Run a Django migration script before migrations (can be repeated)
    --script_after      | Run a Django migration script after migrations (can be repeated)
    --skip_demo_data    | Skip downloading/copying demo data to samba container
    --skip_test_data    | Skip loading test fixtures (test/test_data.json)
    --engine            | Container engine to use: docker (default) or podman
    --test              | Use development/test compose file and sample data

Examples:
    Deploy production container pointing to an external DB/Samba:
    bash $0 --install_conf conf/my_prod_settings.txt

    Deploy production with per-service settings:
    bash $0 --install_conf_map app,conf/docker_production_platform_settings.txt --install_conf_map iskylims_app,conf/docker_production_iskylims_settings.txt

    Upgrade an existing production deployment using the same database:
    bash $0 --install_conf conf/my_prod_settings.txt --action upgrade

    Install demo container system with local services
    bash $0 --test

    Install test stack from current local committed sources without checking out a branch in-container
    bash $0 --test --git_revision current

    Provide already downloaded data from Zenodo (compressed) for test environment
    bash $0 --demo_data /path/to/iskylims_demo_data.tar.gz

EOF
}

# translate long options to short
reset=true

for arg in "$@"
do
    if [ -n "$reset" ]; then
      unset reset
      set --      # this resets the "$@" array so we can rebuild it
    fi
    case "$arg" in
        # OPTIONAL
        --demo_data)         set -- "$@" -d ;;
        --git_revision)      set -- "$@" -g ;;
        --compose_file)      set -- "$@" -c ;;
        --install_conf)      set -- "$@" -s ;;
        --install_conf_map)  set -- "$@" -j ;;
        --action)            set -- "$@" -a ;;
        --script)            set -- "$@" -m ;;
        --script_before)     set -- "$@" -b ;;
        --script_after)      set -- "$@" -f ;;
        --skip_demo_data)    set -- "$@" -n ;;
        --skip_test_data)    set -- "$@" -t ;;
        --test)              set -- "$@" -p ;;
        --engine)            set -- "$@" -e ;;

        # ADDITIONAL
        --help)              set -- "$@" -h ;;
        --version)           set -- "$@" -v ;;
        # PASSING VALUE IN PARAMETER
        *)                   set -- "$@" "$arg" ;;
    esac
done

# SETTING DEFAULT VALUES
demo_data=false
git_revision="main"
compose_file=""
install_conf=""
install_conf_container=""
install_conf_map_entries=()
skip_demo_data=""
skip_test_data=""
mode="production"
action="install"
run_script=false
run_script_before=false
migration_script=()
migration_script_before=()
engine="docker"

ENGINE_CMD=()
COMPOSE_CMD=()

set_engine() {
    if [ "$engine" = "docker" ]; then
        if ! command -v docker >/dev/null 2>&1; then
            echo "docker not found. Install docker or use --engine podman."
            exit 1
        fi
        ENGINE_CMD=("docker")
        COMPOSE_CMD=("docker" "compose")
    else
        if ! command -v podman >/dev/null 2>&1; then
            echo "podman not found. Install podman or use --engine docker."
            exit 1
        fi
        ENGINE_CMD=("podman")
        if command -v podman-compose >/dev/null 2>&1; then
            COMPOSE_CMD=("podman-compose")
        elif podman compose version >/dev/null 2>&1; then
            COMPOSE_CMD=("podman" "compose")
        else
            echo "podman compose not available. Install podman-compose or use --engine docker."
            exit 1
        fi
    fi
}

engine_exec() {
    "${ENGINE_CMD[@]}" "$@"
}

compose_exec() {
    "${COMPOSE_CMD[@]}" "$@"
}

# PARSE VARIABLE ARGUMENTS WITH getopts
options=":d:g:c:s:j:a:m:b:f:e:vhntp"
while getopts $options opt; do
    case $opt in
        d)
            demo_data=$OPTARG
            ;;
        g)
            git_revision=$OPTARG
            ;;
        c)
            compose_file=$OPTARG
            ;;
        s)
            install_conf=$OPTARG
            ;;
        j)
            install_conf_map_entries+=("$OPTARG")
            ;;
        a)
            action=$OPTARG
            if [[ "$action" != "install" && "$action" != "upgrade" ]]; then
                echo "Invalid action '$action'. Use install or upgrade."
                exit 1
            fi
            ;;
        m)
            run_script=true
            migration_script+=("$OPTARG")
            ;;
        b)
            run_script_before=true
            migration_script_before+=("$OPTARG")
            ;;
        e)
            engine=$OPTARG
            if [[ "$engine" != "docker" && "$engine" != "podman" ]]; then
                echo "Invalid engine '$engine'. Use docker or podman."
                exit 1
            fi
            ;;
        f)
            run_script=true
            migration_script+=("$OPTARG")
            ;;
        n)
            skip_demo_data=true
            ;;
        t)
            skip_test_data=true
            ;;
        p)
            mode="test"
            ;;
        h)
            usage
            exit 1
            ;;
        v)
            echo $RELECOVPLATFORM_VERSION
            exit 1
            ;;
        \?)
            echo "Invalid Option: -$OPTARG" 1>&2
            usage
            exit 1
            ;;
        : )
            echo "Option -$OPTARG requires an argument." >&2
            exit 1
            ;;
        * )
            echo "Unimplemented option: -$OPTARG" >&2;
            exit 1
            ;;
    esac
done
shift $((OPTIND-1))

if [ "$mode" = "test" ]; then
    if [ -z "$compose_file" ]; then
        compose_file="docker-compose.test.yml"
    fi
else
    if [ -z "$compose_file" ]; then
        compose_file="docker-compose.prod.yml"
    fi
fi

if [ -z "$skip_demo_data" ]; then
    if [ "$mode" = "test" ]; then
        skip_demo_data=false
    else
        skip_demo_data=true
    fi
fi

if [ -z "$skip_test_data" ]; then
    if [ "$mode" = "test" ]; then
        skip_test_data=false
    else
        skip_test_data=true
    fi
fi

if [ "$action" = "upgrade" ]; then
    skip_demo_data=true
    skip_test_data=true
fi

if [ ! -f "$compose_file" ]; then
    echo "Compose file '$compose_file' not found"
    exit 1
fi

repo_root="$(pwd)"
temp_install_conf_files=()
declare -A service_install_conf_input=()
declare -A install_conf_host_by_service=()
declare -A install_conf_container_by_service=()
declare -A local_head_hash_by_service=()
declare -A local_head_short_by_service=()
declare -A image_id_before_by_service=()
declare -A image_id_after_by_service=()
install_services=("iskylims_app" "app")

cleanup_temp_confs() {
    local f
    for f in "${temp_install_conf_files[@]}"; do
        if [ -n "$f" ] && [ -f "$f" ]; then
            rm -f "$f"
        fi
    done
}
trap cleanup_temp_confs EXIT

default_service_install_conf() {
    case "$1" in
        iskylims_app) echo "conf/docker_test_settings.txt" ;;
        app) echo "conf/docker_test_settings.txt" ;;
        *) echo "conf/docker_test_settings.txt" ;;
    esac
}

service_build_context_dir() {
    case "$1" in
        app) echo "$repo_root" ;;
        iskylims_app) echo "$repo_root/../relecov-iskylims" ;;
        *) echo "$repo_root" ;;
    esac
}

service_is_install_target() {
    local wanted="$1"
    local s
    for s in "${install_services[@]}"; do
        if [ "$s" = "$wanted" ]; then
            return 0
        fi
    done
    return 1
}

prepare_service_conf() {
    local svc="$1"
    local conf_value="$2"
    local service_context_dir=""
    local host_path="$conf_value"
    local resolved_path="$conf_value"
    local temp_path=""

    service_context_dir="$(service_build_context_dir "$svc")"
    if [ ! -d "$service_context_dir" ]; then
        echo "Build context directory '$service_context_dir' for service '$svc' not found"
        exit 1
    fi

    if [[ "$resolved_path" != /* ]]; then
        host_path="$repo_root/$resolved_path"
    else
        host_path="$resolved_path"
    fi

    if [ ! -f "$host_path" ]; then
        echo "Install configuration '$conf_value' for service '$svc' not found"
        exit 1
    fi

    if [[ "$host_path" = /* ]] && [[ "$host_path" != "$service_context_dir/"* ]]; then
        temp_path="$service_context_dir/.tmp_docker_install_conf_${svc}_$$.txt"
        echo "Copying $host_path into temporary file $temp_path for service '$svc'."
        cp "$host_path" "$temp_path"
        host_path="$temp_path"
        temp_install_conf_files+=("$temp_path")
    fi

    if [[ "$host_path" = "$service_context_dir/"* ]]; then
        install_conf_container="${host_path#$service_context_dir/}"
    else
        install_conf_container="$host_path"
    fi

    install_conf_host_by_service["$svc"]="$host_path"
    install_conf_container_by_service["$svc"]="$install_conf_container"
}

for map_entry in "${install_conf_map_entries[@]}"; do
    svc_name="${map_entry%%,*}"
    conf_name="${map_entry#*,}"
    if [ -z "$svc_name" ] || [ -z "$conf_name" ] || [ "$svc_name" = "$map_entry" ]; then
        echo "Invalid --install_conf_map value '$map_entry'. Expected format: service,path"
        exit 1
    fi
    if ! service_is_install_target "$svc_name"; then
        echo "Unknown service '$svc_name' in --install_conf_map. Valid services: ${install_services[*]}"
        exit 1
    fi
    service_install_conf_input["$svc_name"]="$conf_name"
done

for target_service in "${install_services[@]}"; do
    chosen_conf="${service_install_conf_input[$target_service]}"
    if [ -z "$chosen_conf" ]; then
        if [ -n "$install_conf" ]; then
            chosen_conf="$install_conf"
        elif [ "$mode" = "test" ]; then
            chosen_conf="$(default_service_install_conf "$target_service")"
        else
            echo "Production deployments require --install_conf or --install_conf_map for service '$target_service'."
            exit 1
        fi
    fi
    prepare_service_conf "$target_service" "$chosen_conf"
done

set_engine

# Check if a service exists in the compose file
#
# Parameters:
#   $1 - Service name to check
#
# Returns:
#   0 if the service exists, 1 otherwise
service_exists() {
    compose_exec -f "$compose_file" config --services 2>/dev/null | grep -Fxq "$1"
}

# Return the name of the container for a given service name.
# The container name is different based on whether we are in test mode or not.
#
# Parameters:
#   $1 - Service name to return the container name for
#
# Returns:
#   The name of the container for the given service name
service_container_name() {
    local service_name="$1"
    if [ "$mode" = "test" ]; then
        case "$service_name" in
            db) echo "relecov_test_db" ;;
            iskylims_app) echo "relecov_test_iskylims_app" ;;
            app) echo "relecov_test_app" ;;
            nextstrain) echo "relecov_test_nextstrain" ;;
            *) echo "" ;;
        esac
    else
        case "$service_name" in
            iskylims_app) echo "relecov_iskylims_app" ;;
            app) echo "relecov_app" ;;
            nextstrain) echo "relecov_nextstrain" ;;
            *) echo "" ;;
        esac
    fi
}

# Resolve the container ID for a given service name.
#
# Parameters:
#   $1 - Service name to resolve the container ID for
#
# Returns:
#   The container ID for the given service name, or an error code if unable to resolve.
#
# Errors:
#   1 - Unable to resolve container ID for given service name.
resolve_service_container() {
    local service_name="$1"
    local service_container
    local container_name
    container_name="$(service_container_name "$service_name")"

    if [ -n "$container_name" ] && engine_exec inspect -f '{{.Id}}' "$container_name" >/dev/null 2>&1; then
        service_container="$container_name"
    else
        service_container="$(engine_exec ps -a --filter "label=com.docker.compose.service=${service_name}" --format '{{.ID}}' | head -n 1)"
    fi

    if [ -z "$service_container" ]; then
        echo "Error: unable to resolve container ID for service '$service_name'." >&2
        return 1
    fi
    echo "$service_container"
}

# Ensure a service is running.
#
# Parameters:
#   $1 - Service name to ensure is running
#   $2 - Container ID for the service
#
# Returns:
#   The container ID if the service is running, or an error code if unable to resolve.
#
# Errors:
#   1 - Service container does not exist.
#   2 - Service container is not running.
ensure_service_running() {
    local service_name="$1"
    local service_container="$2"
    if ! engine_exec inspect -f '{{.State.Running}}' "$service_container" >/dev/null 2>&1; then
        echo "Error: service '$service_name' container does not exist."
        exit 1
    fi
    if [ "$(engine_exec inspect -f '{{.State.Running}}' "$service_container")" != "true" ]; then
        echo "Error: service '$service_name' container is not running. Showing logs:"
        engine_exec logs --tail 200 "$service_container"
        exit 1
    fi
    echo "$service_container"
}

# Return the repository path for a given service name.
#
# Parameters:
#   $1 - Service name to retrieve the repository path for.
#
# Returns:
#   The repository path for the given service name.
#
# Errors:
#   1 - Unknown service name passed to the function.
service_repo_path() {
    case "$1" in
        iskylims_app) echo "/srv/iskylims" ;;
        app) echo "/srv/relecov-platform" ;;
        *) echo "Error: unknown service '$1'" >&2; exit 1 ;;
    esac
}

service_install_path() {
    case "$1" in
        iskylims_app) echo "/opt/iskylims" ;;
        app) echo "/opt/relecov-platform" ;;
        *) echo "Error: unknown service '$1'" >&2; exit 1 ;;
    esac
}

compose_service_image_id() {
    compose_exec -f "$compose_file" images -q "$1" 2>/dev/null | tail -n 1
}

print_local_source_diagnostics() {
    local service_name="$1"
    local service_context_dir=""
    service_context_dir="$(service_build_context_dir "$service_name")"

    echo "Local source diagnostics for $service_name:"
    if command -v git >/dev/null 2>&1 && git -C "$service_context_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        local_head_hash_by_service["$service_name"]="$(git -C "$service_context_dir" rev-parse HEAD)"
        local_head_short_by_service["$service_name"]="$(git -C "$service_context_dir" rev-parse --short HEAD)"
        echo "  local HEAD: $(git -C "$service_context_dir" log -1 --oneline)"
        echo "  local HEAD hash: ${local_head_hash_by_service[$service_name]}"
    else
        echo "  local git metadata unavailable"
    fi
}

print_existing_artifact_diagnostics() {
    local service_name="$1"
    echo "Image diagnostics before build for $service_name:"
    image_id_before_by_service["$service_name"]="$(compose_service_image_id "$service_name")"
    if [ -n "${image_id_before_by_service[$service_name]}" ]; then
        echo "  image before build: ${image_id_before_by_service[$service_name]}"
    else
        echo "  image before build: none"
    fi
}

print_service_image_after_build() {
    local service_name="$1"
    local previous_id="${image_id_before_by_service[$service_name]}"
    echo "Image diagnostics after build for $service_name:"
    image_id_after_by_service["$service_name"]="$(compose_service_image_id "$service_name")"
    if [ -n "${image_id_after_by_service[$service_name]}" ]; then
        echo "  image after build: ${image_id_after_by_service[$service_name]}"
        if [ -n "$previous_id" ] && [ "$previous_id" = "${image_id_after_by_service[$service_name]}" ]; then
            echo "  image id check: unchanged"
        elif [ -n "$previous_id" ] && [ "$previous_id" != "${image_id_after_by_service[$service_name]}" ]; then
            echo "  image id check: changed"
        else
            echo "  image id check: created"
        fi
    else
        echo "  image after build: not found"
    fi
}

print_container_source_diagnostics() {
    local service_name="$1"
    local service_container="$2"
    local label="$3"
    local service_repo=""
    local container_repo_head_hash=""
    local container_repo_head_short=""

    service_repo="$(service_repo_path "$service_name")"
    echo "$label"
    container_repo_head_hash="$(engine_exec exec "$service_container" sh -lc "
        if [ -d '$service_repo/.git' ]; then
            cd '$service_repo' && git rev-parse HEAD
        fi
    " 2>/dev/null | tail -n 1)"
    container_repo_head_short="$(engine_exec exec "$service_container" sh -lc "
        if [ -d '$service_repo/.git' ]; then
            cd '$service_repo' && git rev-parse --short HEAD
        fi
    " 2>/dev/null | tail -n 1)"
    if [ -n "$container_repo_head_hash" ]; then
        echo "  container /srv HEAD hash: $container_repo_head_hash"
    fi
    if [ -n "${local_head_hash_by_service[$service_name]}" ] && [ -n "$container_repo_head_hash" ]; then
        if [ "${local_head_hash_by_service[$service_name]}" = "$container_repo_head_hash" ]; then
            echo "  HEAD check: OK local=${local_head_short_by_service[$service_name]} container=$container_repo_head_short"
        else
            echo "  HEAD check: MISMATCH local=${local_head_short_by_service[$service_name]} container=$container_repo_head_short"
        fi
    fi
    engine_exec exec "$service_container" sh -lc "
        echo '  $service_repo HEAD:'
        if [ -d '$service_repo/.git' ]; then
            cd '$service_repo' && git log -1 --oneline
        else
            echo 'not a git checkout'
        fi
    " || true
}

# Remove stale test containers left over from previous runs.
#
# This function will only be executed in "test" mode when the engine is "podman".
#
# Parameters:
#   None
#
# Returns:
#   None
#
# Errors:
#   None
cleanup_stale_test_containers() {
    if [ "$mode" != "test" ] || [ "$engine" != "podman" ]; then
        return 0
    fi

    local svc cname cstate
    for svc in db iskylims_app app nextstrain samba; do
        cname="$(service_container_name "$svc")"
        if [ -z "$cname" ]; then
            continue
        fi
        if engine_exec inspect -f '{{.Id}}' "$cname" >/dev/null 2>&1; then
            cstate="$(engine_exec inspect -f '{{.State.Status}}' "$cname" 2>/dev/null || true)"
            if [ "$cstate" != "running" ]; then
                echo "Removing stale test container '$cname' (state: ${cstate:-unknown})"
                engine_exec rm -f "$cname" >/dev/null 2>&1 || true
            fi
        fi
    done
}

cleanup_stale_test_containers

echo "Deploying containers (compose file: $compose_file) with INSTALL_TYPE=dep and GIT_REVISION=$git_revision..."
for target_service in "${install_services[@]}"; do
    if service_exists "$target_service"; then
        service_install_conf="${install_conf_container_by_service[$target_service]}"
        print_local_source_diagnostics "$target_service"
        print_existing_artifact_diagnostics "$target_service"
        echo "Building $target_service with INSTALL_CONF=$service_install_conf"
        INSTALL_TYPE="dep" GIT_REVISION="$git_revision" INSTALL_CONF="$service_install_conf" \
            compose_exec -f "$compose_file" build --no-cache \
            --build-arg INSTALL_TYPE="dep" \
            --build-arg GIT_REVISION="$git_revision" \
            --build-arg INSTALL_CONF="$service_install_conf" \
            "$target_service"
        print_service_image_after_build "$target_service"
    fi
done
compose_exec -f "$compose_file" up -d

echo "Waiting 20 seconds for starting database and web services..."
sleep 20
# Set uid and gid for app user in the container, to ensure runtime directories are created with correct ownership
# If the user has specified custom values for APP_UID and APP_GID in env variables, these will be used
# Otherwise, default to 1212 which is the value used in the Dockerfile.
app_uid="${APP_UID:-1212}"
app_gid="${APP_GID:-1212}"

script_args_before=""
if [ "$run_script_before" = true ]; then
    for val in "${migration_script_before[@]}"; do
        script_args_before+=" --script_before $(printf '%q' "$val")"
    done
fi

script_args_after=""
if [ "$run_script" = true ]; then
    for val in "${migration_script[@]}"; do
        script_args_after+=" --script_after $(printf '%q' "$val")"
    done
fi

installed_iskylims=false
installed_platform=false

for target_service in "${install_services[@]}"; do
    if ! target_container="$(resolve_service_container "$target_service")"; then
        exit 1
    fi
    ensure_service_running "$target_service" "$target_container"
    print_container_source_diagnostics "$target_service" "$target_container" "Container diagnostics after startup for $target_service:"
    target_repo_path="$(service_repo_path "$target_service")"
    target_install_path="$(service_install_path "$target_service")"

    echo "Ensuring runtime directories for $target_service are writable by ${app_uid}:${app_gid}"
    engine_exec exec -u 0 -it "$target_container" sh -lc "mkdir -p ${target_install_path}/documents ${target_install_path}/logs ${target_install_path}/static ${target_install_path}/cron ${target_install_path}/tmp && chown -R ${app_uid}:${app_gid} ${target_install_path}/documents ${target_install_path}/logs ${target_install_path}/static ${target_install_path}/cron ${target_install_path}/tmp"

    host_install_conf_path="${install_conf_host_by_service[$target_service]}"
    service_install_conf="${install_conf_container_by_service[$target_service]}"
    container_install_conf_path="$service_install_conf"
    if [[ "$container_install_conf_path" != /* ]]; then
        container_install_conf_path="${target_repo_path}/$container_install_conf_path"
    fi

    if ! engine_exec exec -it "$target_container" test -f "$container_install_conf_path"; then
        echo "Copying install configuration into $target_service at $container_install_conf_path"
        if [ ! -f "$host_install_conf_path" ]; then
            echo "Error: host install configuration not found for $target_service at $host_install_conf_path"
            exit 1
        fi
        engine_exec cp "$host_install_conf_path" "${target_container}:$container_install_conf_path"
    fi

    if [ "$action" = "upgrade" ]; then
        echo "Running install.sh upgrade in $target_service"
        engine_exec exec -it "$target_container" bash -c "cd $target_repo_path && bash install.sh --upgrade app --git_revision \"$git_revision\" --conf \"$service_install_conf\" --skip_apache_restart$script_args_before$script_args_after"
    else
        echo "Running install.sh install in $target_service"
        engine_exec exec -it "$target_container" bash -c "cd $target_repo_path && bash install.sh --install app --git_revision \"$git_revision\" --conf \"$service_install_conf\" --skip_apache_restart$script_args_before$script_args_after"
    fi

    print_container_source_diagnostics "$target_service" "$target_container" "Container diagnostics after install.sh for $target_service:"

    if ! engine_exec exec -it "$target_container" test -f "$target_install_path/manage.py"; then
        echo "Error: $target_install_path/manage.py not found after install.sh for service $target_service. Showing logs:"
        engine_exec logs --tail 200 "$target_container"
        exit 1
    fi

    if [ "$target_service" = "iskylims_app" ]; then
        installed_iskylims=true
        if [ "$skip_test_data" = false ]; then
            if engine_exec exec -it "$target_container" test -f test/test_data.json; then
                engine_exec exec -it "$target_container" python3 manage.py loaddata test/test_data.json
            else
                echo "No test/test_data.json found in $target_service. Skipping fixture load."
            fi
        else
            echo "Skipping test data fixtures for $target_service as requested"
        fi
    fi

    if [ "$target_service" = "app" ]; then
        installed_platform=true
    fi
done

if [ "$installed_iskylims" = true ] && [ "$skip_demo_data" = false ] && service_exists "samba"; then
    echo "Downloading and copying test files to the Samba container"
    if [ "$demo_data" == "false" ]; then
        wget https://zenodo.org/record/8091169/files/iskylims_demo_data.tar.gz
        demo_data="./iskylims_demo_data.tar.gz"
    fi
    engine_exec cp "$demo_data" samba:/mnt
    engine_exec exec -it samba tar -xf /mnt/iskylims_demo_data.tar.gz -C /mnt
    engine_exec exec -it samba sh -lc '
        for root in /mnt/test_ngs_data /mnt/Runs; do
            if [ -d "$root" ]; then
                find "$root" -type d -exec chmod o+rx {} +
                find "$root" -type f -exec chmod o+r {} +
            fi
        done
    '

    echo "Deleting compressed test file"
    engine_exec exec -it samba rm /mnt/iskylims_demo_data.tar.gz

    if [ "$demo_data" == "false" ]; then
        rm -f "$demo_data"
    fi
else
    echo "Skipping Samba demo data load (flag enabled or service not present)"
fi

echo "Skipping crontab add/start (cron is managed by the container entrypoint)"

dns_url=""
local_ip=""
host_install_conf_path="${install_conf_host_by_service[app]}"
if [ -z "$host_install_conf_path" ]; then
    host_install_conf_path="${install_conf_host_by_service[iskylims_app]}"
fi
if [ -f "$host_install_conf_path" ]; then
    dns_url=$(grep -E "^DNS_URL=" "$host_install_conf_path" | tail -n 1 | cut -d= -f2- | sed "s/^['\"]//;s/['\"]$//")
    local_ip=$(grep -E "^LOCAL_SERVER_IP=" "$host_install_conf_path" | tail -n 1 | cut -d= -f2- | sed "s/^['\"]//;s/['\"]$//")
fi

access_urls=()
if [ -n "$dns_url" ] && [ "$dns_url" != "*" ]; then
    if [ "$installed_iskylims" = true ]; then
        access_urls+=("iSkyLIMS: http://${dns_url}:8001")
    fi
    if [ "$installed_platform" = true ]; then
        access_urls+=("RELECOV Platform: http://${dns_url}:8000")
    fi
fi
if [ -n "$local_ip" ] && [ "$local_ip" != "*" ]; then
    if [ "$installed_iskylims" = true ]; then
        access_urls+=("iSkyLIMS: http://${local_ip}:8001")
    fi
    if [ "$installed_platform" = true ]; then
        access_urls+=("RELECOV Platform: http://${local_ip}:8000")
    fi
fi
if [ ${#access_urls[@]} -eq 0 ]; then
    if [ "$installed_iskylims" = true ]; then
        access_urls+=("iSkyLIMS: http://localhost:8001")
    fi
    if [ "$installed_platform" = true ]; then
        access_urls+=("RELECOV Platform: http://localhost:8000")
    fi
fi

echo "You can now access services via: ${access_urls[*]}"
