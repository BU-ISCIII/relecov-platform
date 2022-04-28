#!/bin/bash

#=============================================================
# HEADER
#=============================================================

#INSTITUTION:ISCIII
#CENTRE:BU-ISCIII
#AUTHOR: Luis Chapado
SCRIPT_VERSION=0.1.0
#CREATED: 18 April 2022
#
#
#DESCRIPTION: This script install on your local server the latest stable
#   version of relecov-platform application 
#
#
#================================================================
# END_OF_HEADER
#================================================================

RELECOVPLATFORM_VERSION="0.1.0"
. ./install_settings.txt

db_check(){
    mysqladmin -h $DB_SERVER_IP -u$DB_USER -p$DB_PASS -P$DB_PORT processlist >null ###user should have mysql permission on remote server.

    if ! [ $? -eq 0 ]; then
        echo -e "${RED}ERROR : Unable to connect to database. Check if your database is running and accessible${NC}"
        exit 1
    fi
    RESULT=`mysqlshow --user=$DB_USER --password=$DB_PASS --host=$DB_SERVER_IP --port=$DB_PORT | grep -o Relecov`

    if  ! [ "$RESULT" == "Relecov" ] ; then
        echo -e "${RED}ERROR : Relecov database is not defined yet ${NC}"
        echo -e "${RED}ERROR : Create Relecov database on your mysql server and run again the installation script ${NC}"
        exit 1    
    fi
}

apache_check(){
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

#================================================================
# MAIN_BODY
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

echo "Checking main requirements"
db_check
echo "Successful check for database"
apache_check
echo "Successful check for apache"
linux_distribution=$(lsb_release -i | cut -f 2-)#Linux version
#================================================================

read -p "Are you sure you want to install Relecov-platform in this server? " -n 1 -r
echo    # (optional) move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]] ; then
    exit 1
fi

#================================================================
if [[ $linux_distribution == "Ubuntu" ]]; then 
    echo "Software installation for Ubuntu"
    apt-get update && apt-get upgrade -y
    apt-get install -y \
        lightdm git apt-utils libcairo2 libcairo2-dev  wget gnuplot python3-pip \
        libmysqlclient-dev apache2-dev vim libapache2-mod-wsgi-py3
    #apt-get install build-essential  -y 
    #apt-get install libghc-zlib-dev libbz2-dev libssl1.0-dev -y
    #apt-get install git libpango1.0 libpango1.0-dev   -y
fi

if [[ $linux_distribution == "Centos" ]]; then 
    echo "Software installation for Centos"
    yum groupinstall “Development tools”
    yum install zlib-devel bzip2-devel sqlite sqlite-devel openssl-devel
    yum install git libcairo2 libcairo2-dev libpango1.0 libpango1.0-dev wget gnuplot
fi

echo "relecov-platform installation"
cd /opt/relecov-platform
git checkout master

mkdir -p /opt/relecov-platform/logs

# install virtual environment
if [[ $linux_distribution == "Ubuntu" ]]; then 
    echo "Creating virtual environment"
    pip3 install virtualenv 
    virtualenv --python=/usr/bin/python3 virtualenv
    
    
fi

if [[ $linux_distribution == "Centos" ]]; then 
    echo "Creating virtual environment"
    cd /opt/python/3.6.4/bin
    ./pip3 install virtualenv 
    virtualenv --python=/usr/bin/python3 virtualenv
    
    
fi

source virtualenv/bin/activate
#cd /srv/iSkyLIMS
#/opt/python/3.6.4/bin/virtualenv --python=/opt/python/3.6.4/bin/python3.6 virtualenv

# Starting iSkyLIMS
python3 -m pip install -r conf/requirements.txt
django-admin startproject relecov-platform .
grep ^SECRET relecov-platform/settings.py > ~/.secret


# Copying config files and script
cp conf/settings.py /opt/relecov-platform/relecov_platform/settings.py
cp conf/urls.py /opt/relecov-platform/relecov_platform/

sed -i "/^SECRET/c\\$(cat ~/.secret)" relecov_platform/settings.py
sed -i "s/djangouser/${DB_USER}/g" relecov_platform/settings.py
sed -i "s/djangopass/${DB_PASS}/g" relecov_platform/settings.py
sed -i "s/djangohost/${DB_SERVER_IP}/g" relecov_platform/settings.py
sed -i "s/djangoport/${DB_PORT}/g" relecov_platform/settings.py

sed -i "s/emailhostserver/${EMAIL_HOST_SERVER}/g" relecov_platform/settings.py
sed -i "s/emailport/${EMAIL_PORT}/g" relecov_platform/settings.py
sed -i "s/emailhostuser/${EMAIL_HOST_USER}/g" relecov_platform/settings.py
sed -i "s/emailhostpassword/${EMAIL_HOST_PASSWORD}/g" relecov_platform/settings.py
sed -i "s/emailhosttls/${EMAIL_USE_TLS}/g" relecov_platform/settings.py
sed -i "s/localserverip/${LOCAL_SERVER_IP}/g" relecov_platform/settings.py


echo "Creating the database structure for relecov-platform"
python3 manage.py migrate
python3 manage.py makemigrations django_utils relecov_core 
python3 manage.py migrate

python3 manage.py collectstatic

echo "Change owner of files to Apache user"
chown -R www-data:www-data /opt/relecov-platform

#echo "Loading in database initial data"
#python3 manage.py loaddata conf/new_installation_loading_tables.json

echo "Running crontab"
python3 manage.py crontab add
mv /var/spool/cron/crontabs/root /var/spool/cron/crontabs/www-data
chown www-data /var/spool/cron/crontabs/www-data 



echo "Updating Apache configuration"
cp conf/apache2.conf /etc/apache2/sites-available/000-default.conf
echo  'LoadModule wsgi_module "/opt/relecov-platform/virtualenv/lib/python3.8/site-packages/mod_wsgi/server/mod_wsgi-py38.cpython-38-x86_64-linux-gnu.so"' >/etc/apache2/mods-available/iskylims.load
cp conf/iskylims.conf /etc/apache2/mods-available/iskylims.conf

# Create needed symbolic links to enable the configurations:

ln -s /etc/apache2/mods-available/iskylims.load /etc/apache2/mods-enabled/
ln -s /etc/apache2/mods-available/iskylims.conf /etc/apache2/mods-enabled/

echo "Creating super user "
python3 manage.py createsuperuser

printf "\n\n%s"
printf "${BLUE}------------------${NC}\n"
printf "%s"
printf "${BLUE}Successfuly iSkyLIMS Installation version: ${RELECOVPLATFORM_VERSION}${NC}\n"
printf "%s"
printf "${BLUE}------------------${NC}\n\n"



