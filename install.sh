#!/bin/bash

PLATFORM_VERSION="1.0.0"
## . ./install_settings.txt

# FIXME: Rename project name with something more generic. "pathoweb-"${project_name}""
usage() {
	cat << EOF
This script install and upgrade the relecov platform application.

usage : $0 --upgrade --git_revision dev --conf
	Optional input data:
    --install       | Define the type of installation full/dep/app
    --upgrade       | Upgrade the relecov application full/dep/app
    --git_revision  | Git revision name to run (it can be git branch, git version tag or commit SHA)
    --conf          | Select custom configuration file. Default: ./install_settings.txt
    --tables        | Load the first inital tables for upgrades in conf folder
    --script        | Run a migration script.
    --docker        | Specific installation for docker compose configuration.


Examples:
    To install only software dependencies for relecov application
    sudo $0 --install dep

    To install only Relecov platform application
    $0 --install app

    Upgrade using develop code
    $0 --upgrade full --git_revision develop

    Upgrade running migration script and update initial tables
    $0 --upgrade full --script <migration_script> --tables

    Make adjustments for apps renaming in upgrade 2.3.0 to 2.3.1
    $0 --upgrade full --ren_app --script <migration_script> --tables
EOF
}

db_check(){
    # user should have mysql permission on remote server.
    mysqladmin -h $DB_SERVER_IP -u$DB_USER -p$DB_PASS -P$DB_PORT processlist > /dev/null

    if ! [ $? -eq 0 ]; then
        echo -e "${RED}ERROR : Unable to connect to database. Check if your database is running and accessible${NC}"
        exit 1
    fi
    RESULT=`mysqlshow --user=$DB_USER --password=$DB_PASS --host=$DB_SERVER_IP --port=$DB_PORT | grep -o $DB_NAME`

    if  ! [ "$RESULT" == "$DB_NAME" ] ; then
        echo -e "${RED}ERROR : $DB_NAME database is not defined yet ${NC}"
        echo -e "${RED}ERROR : Create $DB_NAME database on your mysql server and run again the installation script ${NC}"
        exit 1
    fi
}

apache_check(){
    if [[ $linux_distribution == "Ubuntu" ]]; then
        if ! pidof apache2 > /dev/null ; then
            # web server down, restart the server
            echo "Apache Server is down... Trying to restart Apache"
            systemctl restart apache2.service
            sleep 10
            if pidof apache2 > /dev/null ; then
                echo "Apache Server is up"
            else
                echo -e "${RED}ERROR : Unable to start Apache ${NC}"
                echo -e "${RED}ERROR : Solve the issue with Apache server and run again the installation script ${NC}"
                exit 1
            fi
        fi
    elif [[ $linux_distribution == "CentOs" || $linux_distribution == "RedHatEnterprise" ]]; then
        if ! pidof httpd > /dev/null ; then
            # web server down, restart the server
            echo "Apache Server is down... Trying to restart Apache"
            systemctl restart httpd
            sleep 10
            if pidof httpd > /dev/null ; then
                echo "Apache Server is up"
            else
                echo -e "${RED}ERROR : Unable to start Apache ${NC}"
                echo -e "${RED}ERROR : Solve the issue with Apache server and run again the installation script ${NC}"
                exit 1
            fi
        fi
    fi
}

python_check(){

    python_version=$(su -c $PYTHON_BIN_PATH --version $user)
    if [[ $python_version == "" ]]; then
        echo -e "${RED}ERROR : Python3 is not found in your system ${NC}"
        echo -e "${RED}ERROR : Solve the issue with Python and run again the installation script ${NC}"
        exit 1
    fi
    p_version=$(echo $python_version | cut -d"." -f2)
    if (( $p_version < 7 )); then
        echo -e "${RED}ERROR : Application requieres at least the version 3.7.x of Python3  ${NC}"
        echo -e "Your python version is $python_version"
        echo -e "${RED}ERROR : Solve the issue with Python and run again the installation script ${NC}"
        exit 1
    fi
}

root_check(){
    if [[ $EUID -ne 0 ]]; then
        printf "\n\n%s"
        printf "${RED}------------------${NC}\n"
        printf "%s"
        printf "${RED}Exiting installation. This script must be run as root ${NC}\n"
        printf "\n\n%s"
        printf "${RED}------------------${NC}\n"
        printf "%s"
        exit 1
    fi
}

update_settings_and_urls(){
    # save SECRET KEY at home user directory
    grep ^SECRET $INSTALL_PATH/$PROJECT_NAME/settings.py > ~/.secret

    cp conf/template_settings.py $INSTALL_PATH/$PROJECT_NAME/settings.py
    cp conf/urls.py $INSTALL_PATH/$PROJECT_NAME/
    cp conf/routing.py $INSTALL_PATH/$PROJECT_NAME/
    
    # replacing dummy variables with real values
    sed -i "/^SECRET/c\\$(cat ~/.secret)" $INSTALL_PATH/$PROJECT_NAME/settings.py
    sed -i "s/djangouser/${DB_USER}/g" $INSTALL_PATH/$PROJECT_NAME/settings.py
    sed -i "s/djangopass/${DB_PASS}/g" $INSTALL_PATH/$PROJECT_NAME/settings.py
    sed -i "s/djangohost/${DB_SERVER_IP}/g" $INSTALL_PATH/$PROJECT_NAME/settings.py
    sed -i "s/djangoport/${DB_PORT}/g" $INSTALL_PATH/$PROJECT_NAME/settings.py
    sed -i "s/djangodbname/${DB_NAME}/g" $INSTALL_PATH/$PROJECT_NAME/settings.py

    sed -i "s/emailhostserver/${EMAIL_HOST_SERVER}/g" $INSTALL_PATH/$PROJECT_NAME/settings.py
    sed -i "s/emailport/${EMAIL_PORT}/g" $INSTALL_PATH/$PROJECT_NAME/settings.py
    sed -i "s/emailhostuser/${EMAIL_HOST_USER}/g" $INSTALL_PATH/$PROJECT_NAME/settings.py
    sed -i "s/emailhostpassword/${EMAIL_HOST_PASSWORD}/g" $INSTALL_PATH/$PROJECT_NAME/settings.py
    sed -i "s/emailhosttls/${EMAIL_USE_TLS}/g" $INSTALL_PATH/$PROJECT_NAME/settings.py
    sed -i "s/localserverip/${LOCAL_SERVER_IP}/g" $INSTALL_PATH/$PROJECT_NAME/settings.py
    sed -i "s/localhost/${DNS_URL}/g" $INSTALL_PATH/$PROJECT_NAME/settings.py
}

upgrade_venv(){
    echo "activate the virtualenv"
    source virtualenv/bin/activate
    echo "Installing required python packages"
    python -m pip install --upgrade pip
    python -m pip install -r conf/requirements.txt
}

restore_git_ref() {
    echo "Restoring to initial git reference: $initial_git_ref"
    git checkout "$initial_git_ref" --quiet
}

update_system_deps() {

    if [[ $linux_distribution == "Ubuntu" ]]; then
        echo "Software installation for Ubuntu"
        apt-get update && apt-get upgrade -y
        apt-get install -y \
            apt-utils wget \
            libmysqlclient-dev \
            python3-venv  \
            libpq-dev \
            python3-dev python3-pip python3-wheel \
            apache2-dev\
            gnuplot
    fi

    if [[ $linux_distribution == "CentOS" || $linux_distribution == "RedHatEnterprise" ]]; then
        echo "Software installation for Centos/RedHat"
        yum groupinstall "Development tools"
        yum install zlib-devel bzip2-devel openssl-devel \
                        wget httpd-devel mysql-libs sqlite sqlite-devel \
                        mariadb-devel libffi-devel \
                        gnuplot
    fi

}

# Ensure to recover current git branch/tag/SHA on script exit
initial_git_ref=$(git rev-parse --abbrev-ref HEAD || git rev-parse HEAD)
trap restore_git_ref EXIT

#================================================================
#SET TEMINAL COLORS
#================================================================
YELLOW='\033[0;33m'
WHITE='\033[0;37m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

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
        --install)      set -- "$@" -i ;;
        --upgrade)      set -- "$@" -u ;;
        --script)       set -- "$@" -s ;;
        --tables)       set -- "$@" -t ;;
        --git_revision) set -- "$@" -g ;;
        --conf)         set -- "$@" -c ;;
        --docker)       set -- "$@" -k ;;

    # ADITIONAL
        --help)         set -- "$@" -h ;;
        --version)      set -- "$@" -v ;;
    # PASSING VALUE IN PARAMETER
        *)              set -- "$@" "$arg" ;;
    esac
done

# SETTING DEFAULT VALUES
tables=false
git_branch=$initial_git_ref
conf="./install_settings.txt"
install=true
install_type="full"
upgrade=false
upgrade_type="full"
docker=false

# PARSE VARIABLE ARGUMENTS WITH getops
options=":c:s:i:u:g:tdkvh"
while getopts $options opt; do
	case $opt in
        i ) 
            install=true
            upgrade=false
            if [[ "$OPTARG" -eq "full" || "$OPTARG" -eq "dep" || "$OPTARG" -eq "app" ]]; then
                install_type=$OPTARG
                upgrade_type=$OPTARG
            else
                echo "Upgrade is not set to one valid option. Use: --upgrade full/app/dep"
                exit 1
            fi
            ;;
		u )
            install=false
			upgrade=true
            if [[ "$OPTARG" -eq "full" || "$OPTARG" -eq "dep" || "$OPTARG" -eq "app" ]]; then
                upgrade_type=$OPTARG
                install_type=$OPTARG
            else
                echo "Upgrade is not set to one valid option. Use: --upgrade full/app/dep"
                exit 1
            fi
            ;;
        s )
            run_script=true
            migration_script+=("$OPTARG")
            ;;
        t )
            tables=true
            ;;
		g )
			git_branch=$OPTARG
			;;
        c )
            conf=$OPTARG
            ;;
        k )
            docker=true
		  	;;
		h )
		  	usage
		  	exit 1
		  	;;
		v )
		  	echo $PLATFORM_VERSION
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
#=============================================================================
#                     SETTINGS CHECKINGS
#=============================================================================

if [ ! -f "$conf" ]; then
    printf "\n\n%s"
    printf "${RED}------------------${NC}\n"
    printf "${RED}Unable to start.${NC}\n"
    printf "${RED}Configuration File $conf does not exist.${NC}\n"
    printf "${RED}------------------${NC}\n"
    exit 1
fi

# Read configuration file

. $conf

# Check if git reference (branch, SHA, or tag) exists and checkout
if git rev-parse --verify "$git_branch" >/dev/null 2>&1; then
    if [[ $git_branch != $initial_git_ref ]]; then
        # Check for local changes
        local_changes=$(git status --porcelain)
        if [[ -n $local_changes ]]; then
            printf "\n\n%s"
            printf "${RED}------------------${NC}\n"
            printf "${RED}Unable to switch to $git_branch.${NC}\n"
            printf "${RED}You have local changes that would be overwritten by checkout:${NC}\n"
            printf "${RED}\t'$local_changes'.${NC}\n"
            printf "${RED}Please commit or stash your changes before switching.${NC}\n"
            printf "${RED}------------------${NC}\n"
            exit 1
        else
            printf "${YELLOW}Switching to revision $git_branch.${NC}\n"
            git checkout "$git_branch" --quiet
        fi
    else
        printf "${YELLOW}Using current revision: '$git_branch'.${NC}\n"
    fi
else
    printf "\n\n%s"
    printf "${RED}------------------${NC}\n"
    printf "${RED}Unable to start.${NC}\n"
    printf "${RED}Git reference $git_branch is not defined in ${PWD}.${NC}\n"
    printf "${RED}------------------${NC}\n"
    exit 1
fi
#================================================================
# CHECK REQUIREMENTS BEFORE STARTING INSTALLATION
#================================================================

echo "Checking main requirements"
python_check
printf "${BLUE}Valid version of Python${NC}\n"
if [ $docker == false ]; then
    db_check
    printf "${BLUE}Successful check for database${NC}\n"
    apache_check
    printf "${BLUE}Successful check for apache${NC}\n"
fi

if [ "$install_type" == "full" ] || [ "$install_type" == "dep" ] || [ "$upgrade_type" == "full" ] || [ "$upgrade_type" == "dep" ]; then
    printf "${YELLOW} Checking requirement of root  user when installation is full or dep ${NC}\n"
    root_check
    printf "${BLUE}Successful checking of root user${NC}\n"
fi

#=============================================================================
#                   UPGRADE INSTALLATION
# Check if parameter is passing to script to upgrade the installation
# If "upgrade" parameter is set then the script only execute the upgrade part.
# If other parameter as upgrade is given return usage message and exit
#=============================================================================
if [ $upgrade == true ]; then
    # check if upgrade keyword is given
    if [ ! -d $INSTALL_PATH ]; then
        printf "\n\n%s"
        printf "${RED}------------------${NC}\n"
        printf "${RED}Unable to start the upgrade.${NC}\n"
        printf "${RED}Folder $INSTALL_PATH does not exist.${NC}\n"
        printf "${RED}------------------${NC}\n"
        exit 1
    fi
    #================================================================
    # MAIN_BODY FOR UPGRADE
    #================================================================
    printf "\n\n%s"
    printf "${YELLOW}------------------${NC}\n"
    printf "%s"
    printf "${YELLOW}Starting Relecov Upgrade version: ${PLATFORM_VERSION}${NC}\n"
    printf "%s"
    printf "${YELLOW}------------------${NC}\n\n"
    
    if [ "$upgrade_type" = "full" ] || [ "$upgrade_type" = "dep" ]; then
        
        # Linux distribution
        linux_distribution=$(lsb_release -i | cut -f 2-)
        update_system_deps
        
        if [ -d $INSTALL_PATH/virtualenv ]; then
            read -p "Do you want to remove current virtualenv and reinstall? (Y/N) " -n 1 -r
            echo    # (optional) move to a new line
            if [[ $REPLY =~ ^[Yy]$ ]] ; then
                rm -rf $INSTALL_PATH/virtualenv
                rsync -rlv conf/requirements.txt $INSTALL_PATH/conf/requirements.txt
                cd $INSTALL_PATH
                bash -c "$PYTHON_BIN_PATH -m venv virtualenv"
                upgrade_venv
                cd -
            else
                rsync -rlv conf/requirements.txt $INSTALL_PATH/conf/requirements.txt
                cd $INSTALL_PATH
                upgrade_venv
                cd -
            fi    
        else
            echo "There is no virtualenv to upgrade in $INSTALL_PATH."
            read -p "Do you want to create a new virtualenv and reinstall? (Y/N) " -n 1 -r
            echo    # (optional) move to a new line
            if [[ $REPLY =~ ^[Yy]$ ]] ; then
                rsync -rlv conf/requirements.txt $INSTALL_PATH/conf/requirements.txt
                cd $INSTALL_PATH
                bash -c "$PYTHON_BIN_PATH -m venv virtualenv"
                upgrade_venv
                cd -
            else
                echo "Exiting..."
                exit 0
            fi
        fi
    fi

    if [ "$upgrade_type" = "full" ] || [ "$upgrade_type" = "app" ]; then

        # update installation by sinchronize folders
        echo "Copying files to installation folder"
        rsync -rlv conf/ $INSTALL_PATH/conf/
        rsync -rlv --fuzzy --delay-updates --delete-delay \
            --exclude "logs" --exclude "documents" --exclude "migrations" --exclude "__pycache__" \
            README.md LICENSE conf $REQUIRED_MODULES $INSTALL_PATH/
            
        # update the settings.py and the main urls
        echo "Update settings and url file."
        update_settings_and_urls

        cd $INSTALL_PATH
        echo "activate the virtualenv"
        source virtualenv/bin/activate

        if python manage.py makemigrations | grep -q "No changes"; then
            # check for pending migrations
            if ./manage.py showmigrations | grep '\[ \]'; then
                echo "There are pending migrations"
                read -p "Do you want to update database with the pending migrations? (Y/N) " -n 1 -r
                echo    #  move to a new line
                if [[ ! $REPLY =~ ^[Yy]$ ]] ; then
                    echo "Continue running script without running migrate command."
                else
                    echo "Running migrate..."
                    python manage.py migrate
                    echo "Done migrate command."
                fi
            else
                echo "No migration is required"
            fi
        else
            read -p "Do you want to proceed with the migrate command? (Y/N) " -n 1 -r
            echo    # (optional) move to a new line
            if [[ ! $REPLY =~ ^[Yy]$ ]] ; then
                echo "Exiting without running migrate command."
                exit 1
            fi
            echo "Running migrate..."
            python manage.py migrate
            echo "Done migrate command."
        fi

        echo "Running collect statics..."
        python manage.py collectstatic
        echo "Done collect statics"

        if [ $tables == true ] ; then
            echo "Loading pre-filled tables..."
            python manage.py loaddata conf/first_install_tables.json
            echo "Done loading pre-filled tables..."
        fi

        if [ $run_script ]; then
            for val in "${migration_script[@]}"; do
                echo "Running migration script: $val"
                python manage.py runscript $val
                echo "Done migration script: $val"
            done
        fi

        cd -

        # Linux distribution
        linux_distribution=$(lsb_release -i | cut -f 2-)

        echo ""
        echo "Restart apache server to update changes"
        if [[ $linux_distribution == "Ubuntu" ]]; then
                apache_daemon="apache2"
        else
                apache_daemon="httpd"
        fi
        
        # systemctl restart $apache_user

        if ! [ $? -eq 0 ]; then
            echo -e "${ORANGE}Apache server restart failed. trying with sudo{NC}"
            sudo systemctl restart $apache_daemon
        fi
    fi
    printf "\n\n%s"
    printf "${BLUE}------------------${NC}\n"
    printf "%s"
    printf "${BLUE}Successfuly upgrade of $PROJECT_NAME version: ${PLATFORM_VERSION}${NC}\n"
    printf "%s"
    printf "${BLUE}------------------${NC}\n\n"
    # exit once upgrade is finished
    exit 0

fi

#================================================================
# INSTALL REPOSITORY REQUIRED SOFTWARE AND PYTHON VIRTUAL ENVIRONMENT
#================================================================

if [ $install == true ]; then

    if [ "$install_type" == "full" ] || [ "$install_type" == "dep" ]; then

        #================================================================
        # MAIN_BODY FOR INSTALL
        #================================================================
        printf "\n\n%s"
        printf "${YELLOW}------------------${NC}\n"
        printf "%s"
        printf "${YELLOW}Starting Relecov Installation version: ${PLATFORM_VERSION}${NC}\n"
        printf "%s"
        printf "${YELLOW}------------------${NC}\n\n"

        user=$SUDO_USER
        group=$(groups | cut -d" " -f1)

        # Find out server Linux distribution
        linux_distribution=$(lsb_release -i | cut -f 2-)

        if [[ $linux_distribution == "Ubuntu" ]]; then
            apache_group="www-data"
        else
            apache_group="apache"
        fi

        echo "Starting $PROJECT_NAME installation"
        if [ -d $INSTALL_PATH ]; then
            echo "There already is an installation of $PROJECT_NAME in $INSTALL_PATH."
            read -p "Do you want to remove current installation and reinstall? (Y/N) " -n 1 -r
            echo    # (optional) move to a new line
            if [[ ! $REPLY =~ ^[Yy]$ ]] ; then
                echo "Exiting without running $PROJECT_NAME installation"
                exit 1
            else
                rm -rf $INSTALL_PATH
            fi
        fi

        echo "Starting $PROJECT_NAME installation"
        if [ -d $INSTALL_PATH ]; then
            echo "There already is an installation of $PROJECT_NAME in $INSTALL_PATH."
            read -p "Do you want to remove current installation and reinstall? (Y/N) " -n 1 -r
            echo    # (optional) move to a new line
            if [[ ! $REPLY =~ ^[Yy]$ ]] ; then
                echo "Exiting without running $PROJECT_NAME installation"
                exit 1
            else
                rm -rf $INSTALL_PATH
            fi
        fi

        update_system_deps

        ## Create the installation folder
        mkdir -p $INSTALL_PATH/conf
        chown -R $user:$apache_group $INSTALL_PATH
        chmod 775 $INSTALL_PATH

        # Copy requirements before moving to install path
        rsync -rlv conf/requirements.txt $INSTALL_PATH/conf/requirements.txt

        cd $INSTALL_PATH
        # install virtual environment
        echo "Creating virtual environment"
        if [ -d $INSTALL_PATH/virtualenv ]; then
            echo "There already is a virtualenv for iskylims in $INSTALL_PATH."
            read -p "Do you want to remove current virtualenv and reinstall? (Y/N) " -n 1 -r
            echo    # (optional) move to a new line
            if [[ $REPLY =~ ^[Yy]$ ]] ; then
                echo "Removing old virtual env and reinstalling"
                rm -rf $INSTALL_PATH/virtualenv
                bash -c "$PYTHON_BIN_PATH -m venv virtualenv"
            else
                echo "virtualenv alredy defined. Skipping."
            fi
        else
            bash -c "$PYTHON_BIN_PATH -m venv virtualenv"
        fi

        echo "activate the virtualenv"
        source virtualenv/bin/activate

        # Install python packages required for relecov-platform
        echo "Installing required python packages"
        python -m pip install wheel
        python -m pip install -r conf/requirements.txt

        cd -

        if [ "$install_type" == "full" ] || [ "$install_type" == "app" ]; then
            printf "\n\n%s"
            printf "${BLUE}------------------${NC}\n"
            printf "%s"
            printf "${BLUE}Software dep are successfuly installed${NC}\n"
            printf "%s"
            printf "${BLUE}------------------${NC}\n\n"
        else
            printf "\n\n%s"
            printf "${BLUE}------------------${NC}\n"
            printf "%s"
            printf "${BLUE}Software dependencies are successfuly installed${NC}\n"
            printf "%s"
            printf "${BLUE}------------------${NC}\n\n"
            printf "\n\n%s"
            printf "${RED}------------------${NC}\n"
            printf "%s"
            printf "${RED}Exiting${NC}\n"
            printf "%s"
            printf "${RED}------------------${NC}\n\n"
            exit 0
        fi
    fi

    #================================================================
    # INSTALL RELECOV PLATFORM APPLICATION
    #================================================================

    if [ "$install_type" == "full" ] || [ "$install_type" == "app" ]; then

        if [ $LOG_TYPE == "symbolic_link" ]; then
            if [ -d $LOG_PATH ]; then
                if [ ! -d $INSTALL_PATH/logs ]; then
                    echo "Deleting existing symbolin link" 
                    rm $INSTALL_PATH/logs
                fi
                echo "Creating symbolic link to log folder"
                ln -s $LOG_PATH  $INSTALL_PATH/logs
                chmod 775 $LOG_PATH
            else
                echo "Log folder path: $LOG_PATH does not exist. Fix it in the install_settings.txt and run again."
            exit 1
            fi
        else
            if  [ ! -d $INSTALL_PATH/logs ]; then
                mkdir -p $INSTALL_PATH/logs
                chown $user:$apache_group $INSTALL_PATH/logs
                chmod 775 $INSTALL_PATH/logs
            else
                echo "Log folder path: $INSTALL_PATH/logs already exist."
            fi
        fi

        mkdir -p $INSTALL_PATH/$PROJECT_NAME
        rsync -rlv README.md LICENSE conf $REQUIRED_MODULES $INSTALL_PATH/

        cd $INSTALL_PATH

        # Starting platform
        echo "activate the virtualenv"
        source virtualenv/bin/activate

        # Starting Relecov Platform
        echo "Creating $PROJECT_NAME project"
        django-admin startproject $PROJECT_NAME .
        
        # update the settings.py and the main urls
        echo "Updating settings and urls"
        update_settings_and_urls

        if [ $docker == false ]; then
            echo "Creating the database structure for $PROJECT_NAME"
            python manage.py migrate
            python manage.py makemigrations django_plotly_dash $MIGRATION_MODULES
            python manage.py migrate
            echo "Loading in database initial data"
            python manage.py loaddata conf/first_install_tables.json

            echo "Updating Apache configuration"
            if [[ $linux_distribution == "Ubuntu" ]]; then
                cp conf/relecov_apache_ubuntu.conf /etc/apache2/sites-available/000-default.conf
            fi

            if [[ $linux_distribution == "CentOS" || $linux_distribution == "RedHatEnterprise" ]]; then
                cp conf/relecov_apache_centos_redhat.conf /etc/httpd/conf.d/relecov-platform.conf
            fi

            echo "Creating super user "
            python manage.py createsuperuser --username admin
        fi

        # copy static files 
        echo "Run collectstatic"
        python manage.py collectstatic

        cd -

        printf "\n\n%s"
        printf "${BLUE}------------------${NC}\n"
        printf "%s"
        printf "${BLUE}Successfuly $PROJECT_NAME Installation version: ${PLATFORM_VERSION}${NC}\n"
        printf "%s"
        printf "${BLUE}------------------${NC}\n\n"
        
        echo "Installation completed"
        exit 0
    fi
fi

printf "\n\n%s"
printf "${RED}------------------${NC}\n"
printf "%s"
printf "${RED}Invalid installation parameters${NC}\n"
printf "%s"
printf "${RED}------------------${NC}\n\n"
echo "See the usage examples"
usage
exit 1

