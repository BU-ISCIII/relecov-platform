#!/bin/bash

RELECOVPLATFORM_VERSION="1.0.0"
## . ./initial_settings.txt


usage() {
	cat << EOF
This script install and upgrade the relecov platform application.

usage : $0 --upgrade --dev --conf 
	Optional input data:
    --upgrade | Upgrade the relecov application
    --dev     | Use the develop version instead of main release
    --conf    | Select configuration file


Examples: 
    To install relecov application with the main release 
    sudo $0 

    To upgrade using develop code
    $0 --upgrade --dev
EOF
}


db_check(){
	mysqladmin -h $DB_SERVER_IP -u$DB_USER -p$DB_PASS -P$DB_PORT processlist >/tmp/null ###user should have mysql permission on remote server.

    if ! [ $? -eq 0 ]; then
        echo -e "${RED}ERROR : Unable to connect to database. Check if your database is running and accessible${NC}"
        exit 1
    fi
    RESULT=`mysqlshow --user=$DB_USER --password=$DB_PASS --host=$DB_SERVER_IP --port=$DB_PORT | grep -o relecov`

    if  ! [ "$RESULT" == "relecov" ] ; then
        echo -e "${RED}ERROR : Relecov database is not defined yet ${NC}"
        echo -e "${RED}ERROR : Create Relecov database on your mysql server and run again the installation script ${NC}"
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

    python_version=$(su -c python3 --version $user)
    if [[ $python_version == "" ]]; then
        echo -e "${RED}ERROR : Python3 is not found in your system ${NC}"
        echo -e "${RED}ERROR : Solve the issue with Python and run again the installation script ${NC}"
        exit 1
    fi
    p_version=$(echo $python_version | cut -d"." -f2)
    if (( $p_version < 7 )); then
        echo -e "${RED}ERROR : Application requieres at least the version 3.7.x of Python3  ${NC}"
        echo -e "${RED}ERROR : Solve the issue with Python and run again the installation script ${NC}"
        exit 1
    fi
}
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
    ##OPTIONAL
		--upgrade)	set -- "$@"	-u ;;
        --dev)      set -- "$@" -d ;;
        --conf)     set -- "$@" -c ;;

    ## ADITIONAL
        --help)     set -- "$@" -h ;;
        --version)  set -- "$@" -v ;;
    ## PASSING VALUE IN PARAMETER
        *)          set -- "$@" "$arg" ;;
    esac
done

#SETTING DEFAULT VALUES
upgrade=false
git_branch="main"
conf_file="./initial_settings.txt"

#PARSE VARIABLE ARGUMENTS WITH getops
options=":c:duvh"
while getopts $options opt; do
	case $opt in
		u )
			upgrade=true
			;;
		d )
			git_branch="develop"
			;;
        c )
		  	conf_file=$OPTARG
		  	;;
		h )
		  	usage
		  	exit 1
		  	;;
		v )
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

#=============================================================================
#                     SETTINGS CHECKINGS
#=============================================================================

if [ ! -f "$conf_file" ]; then 
    printf "\n\n%s"
    printf "${RED}------------------${NC}\n"
    printf "${RED}Unable to start.${NC}\n"
    printf "${RED}Configuration File $conf_file does not exist.${NC}\n"
    printf "${RED}------------------${NC}\n"
    exit 1
fi

# Read configuration file

. $conf_file

# check if branch master/develop is defined and checkout
if [ "`git branch --list $git_branch`" ]; then
    git checkout $git_branch
else
    printf "\n\n%s"
    printf "${RED}------------------${NC}\n"
    printf "${RED}Unable to start.${NC}\n"
    printf "${RED}Git branch $git_branch is not define in ${PWD}.${NC}\n"
    printf "${RED}------------------${NC}\n"
    exit 1
fi

#=============================================================================
#                   UPGRADE INSTALLATION 
# Check if parameter is passing to script to upgrade the installation
# If "upgrade" parameter is set then the script only execute the upgrade part.
# If other parameter as upgrade is given return usage message and exit
#=============================================================================



if [ $upgrade == true ]; then
    # check if upgrade keyword is given
    if [ ! -d $INSTALL_PATH/relecov-platform ]; then
        printf "\n\n%s"
        printf "${RED}------------------${NC}\n"
        printf "${RED}Unable to start the upgrade.${NC}\n"
        printf "${RED}Folder $INSTALL_PATH/relecov-platform does not exist.${NC}\n"
        printf "${RED}------------------${NC}\n"
        exit 1
    fi
    #================================================================
    # MAIN_BODY FOR UPGRADE 
    #================================================================
    printf "\n\n%s"
    printf "${YELLOW}------------------${NC}\n"
    printf "%s"
    printf "${YELLOW}Starting Relecov Upgrade version: ${RELECOVPLATFORM_VERSION}${NC}\n"
    printf "%s"
    printf "${YELLOW}------------------${NC}\n\n"

    # update installation by sinchronize folders
    echo "Copying files to installation folder"
    rsync -rlv README.md LICENSE conf relecov_core relecov_dashboard relecov_documentation $INSTALL_PATH/relecov-platform
    # upgrade database if needed
    cd $INSTALL_PATH/relecov-platform
    echo "activate the virtualenv"
    source virtualenv/bin/activate

    echo "checking for database changes"
    ./manage.py makemigrations
    ./manage.py migrate
    ./manage.py collectstatics
    
    #Linux distribution
    linux_distribution=$(lsb_release -i | cut -f 2-)
    
    echo ""
    echo "Restart apache server to update changes"
    if [[ $linux_distribution == "Ubuntu" ]]; then
        apache_user="apache"
    else
        apache_user="httpd" 
    fi
    sudo systemctl restart $apache_user
    
    printf "\n\n%s"
    printf "${BLUE}------------------${NC}\n"
    printf "%s"
    printf "${BLUE}Successfuly upgrade of Relecov Platform version: ${RELECOVPLATFORM_VERSION}${NC}\n"
    printf "%s"
    printf "${BLUE}------------------${NC}\n\n"

    exit 0
fi

#================================================================
# MAIN_BODY FOR NEW INSTALLATION 
#================================================================

printf "\n\n%s"
printf "${YELLOW}------------------${NC}\n"
printf "%s"
printf "${YELLOW}Starting Relecov Installation version: ${RELECOVPLATFORM_VERSION}${NC}\n"
printf "%s"
printf "${YELLOW}------------------${NC}\n\n"

#================================================================
#CHECK REQUIREMENTS BEFORE STARTING INSTALLATION
#================================================================
# Check that script is run as root
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

user=$SUDO_USER
group=$(groups | cut -d" " -f1)

#Linux distribution
linux_distribution=$(lsb_release -i | cut -f 2-)

echo "Checking main requirements"
python_check
printf "${BLUE}Valid version of Python${NC}\n"
db_check
printf "${BLUE}Successful check for database${NC}\n"
apache_check
printf "${BLUE}Successful check for apache${NC}\n"

#================================================================
## move to develop branch if --dev param

##git checkout develop

#================================================================

read -p "Are you sure you want to install Relecov-platform in this server? (Y/N) " -n 1 -r
echo    # (optional) move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]] ; then
    echo "Exiting without running relecov_platform installation"
    exit 1
fi

#================================================================
if [[ $linux_distribution == "Ubuntu" ]]; then
    echo "Software installation for Ubuntu"
    apt-get update && apt-get upgrade -y
    apt-get install -y \
        apt-utils wget \
        libmysqlclient-dev apache2-dev \
        python3-venv
    # libapache2-mod-wsgi-py3
fi

if [[ $linux_distribution == "CentOS" || $linux_distribution == "RedHatEnterprise" ]]; then
    echo "Software installation for Centos/RedHat"
    yum install zlib-devel bzip2-devel openssl-devel \
                wget httpd-devel mysql-libs
fi

echo "Starting relecov-platform installation"
if [ -d $INSTALL_PATH/relecov-platform ]; then
    echo "There already is an installation of relecov-platform in $INSTALL_PATH."
    read -p "Do you want to remove current installation and reinstall? (Y/N) " -n 1 -r
    echo    # (optional) move to a new line
    if [[ ! $REPLY =~ ^[Yy]$ ]] ; then
        echo "Exiting without running relecov_platform installation"
        exit 1
    else
        rm -rf $INSTALL_PATH/relecov-platform
    fi
fi

## Clone relecov-platform repository
mkdir $INSTALL_PATH/relecov-platform
#git clone https://github.com/BU-ISCIII/relecov-platform.git relecov-platform
rsync -rlv README.md LICENSE conf relecov_core relecov_dashboard relecov_documentation $INSTALL_PATH/relecov-platform

cd $INSTALL_PATH/relecov-platform

## Create apache group if it does not exist.
if ! grep -q apache /etc/group
then
    groupadd apache
fi

## Fix permissions and owners

if [ $LOG_TYPE == "symbolic_link" ]; then
    if [ -d $LOG_PATH ]; then
    	ln -s $LOG_PATH /opt/relecov-platform/logs
	chmod 775 $LOG_PATH
    else
        echo "Log folder path: $LOG_PATH does not exist. Fix it in the initial_settings.txt and run again."
	exit 1
    fi
else
    mkdir -p /opt/relecov-platform/logs
    chown $user:apache /opt/relecov-platform/logs
    chmod 775 /opt/relecov-platform/logs
fi

mkdir -p /opt/relecov-platform/documents
chown $user:apache /opt/relecov-platform/documents
chmod 775 /opt/relecov-platform/documents
mkdir -p /opt/relecov-platform/documents/schemas
chown $user:apache /opt/relecov-platform/documents/schemas
chmod 775 /opt/relecov-platform/documents/schemas
echo "Created folders for logs and documents "

# install virtual environment
echo "Creating virtual environment"
if [ -d $INSTALL_PATH/relecov-platform/virtualenv ]; then
    echo "There already is a virtualenv for relecov-platform in $INSTALL_PATH."
    read -p "Do you want to remove current virtualenv and reinstall? (Y/N) " -n 1 -r
    echo    # (optional) move to a new line
    if [[ ! $REPLY =~ ^[Yy]$ ]] ; then
        rm -rf $INSTALL_PATH/relecov-platform/virtualenv
        bash -c "$PYTHON_BIN_PATH -m venv virtualenv"
    else
        echo "virtualenv alredy defined. Skipping."
    fi
else
    bash -c "$PYTHON_BIN_PATH -m venv virtualenv"
fi

echo "activate the virtualenv"
source virtualenv/bin/activate

# Starting Relecov Platform
echo "Loading python necessary packages"
python3 -m pip install -r conf/requirements.txt
echo ""
echo "Creating relecov_platform project"
django-admin startproject relecov_platform .
grep ^SECRET relecov_platform/settings.py > ~/.secret


# Copying config files and script
cp conf/template_settings.py /opt/relecov-platform/relecov_platform/settings.py
cp conf/urls.py /opt/relecov-platform/relecov_platform/
cp conf/routing.py /opt/relecov-platform/relecov_platform/

sed -i "/^SECRET/c\\$(cat ~/.secret)" relecov_platform/settings.py
sed -i "s/djangouser/${DB_USER}/g" relecov_platform/settings.py
sed -i "s/djangopass/${DB_PASS}/g" relecov_platform/settings.py
sed -i "s/djangohost/${DB_SERVER_IP}/g" relecov_platform/settings.py
sed -i "s/djangoport/${DB_PORT}/g" relecov_platform/settings.py

sed -i "s/localserverip/${LOCAL_SERVER_IP}/g" relecov_platform/settings.py
sed -i "s/dns_url/${DNS_URL}/g" relecov_platform/settings.py

echo "Creating the database structure for relecov-platform"
python3 manage.py migrate
python3 manage.py makemigrations relecov_core django_plotly_dash relecov_dashboard
python3 manage.py migrate

## Adding permissions
chown $user:$group -R relecov_platform

echo "Loading in database initial data"
python3 manage.py loaddata conf/upload_tables.json

echo "Updating Apache configuration"
if [[ $linux_distribution == "Ubuntu" ]]; then
    cp conf/relecov_apache_ubuntu.conf /etc/apache2/sites-available/000-default.conf
fi

if [[ $linux_distribution == "CentOS" || $linux_distribution == "RedHatEnterprise" ]]; then
    cp conf/relecov_apache_centos_redhat.conf /etc/httpd/conf.d/relecov_platform.conf
fi

echo "Creating admin user"
python3 manage.py createsuperuser --username admin

printf "\n\n%s"
printf "${BLUE}------------------${NC}\n"
printf "%s"
printf "${BLUE}Successfuly Relecov Platform Installation version: ${RELECOVPLATFORM_VERSION}${NC}\n"
printf "%s"
printf "${BLUE}------------------${NC}\n\n"

echo "Installation completed"
