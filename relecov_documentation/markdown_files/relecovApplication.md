# Install Relecov application

Relecov application uses Django as the main framework to build the application.


The installation procedure assume that the following requirements are fulfilled:

-  Relecov application has to be installed in a linux server. Tested on Ubuntu 22.04, CentOS 7 and Red Hat 8.
-  Python3.8.10 or higher already installed.
-  Mysql server is eihter installed in the server or remote.
-  Database called **"relecov_platform"** is defined.
-  User is configured to access this database with the right permisions to create/delete/modify tables, index.
-  Apache server must be running in the server
-  iSkyLIMS must be installed. Follow the installation guide defined in github [iSkyLIMS](https://github.com/BU-ISCIII/iSkyLIMS#readme).

For your convinence a installation script was created to perform the software installation 
and the first configuration.

The installation procedue as well as the script are available at github [Relecov-platform](https://github.com/BU-ISCIII/relecov-platform#readme)

## Load setting values on database

## Settings
There are some settings that could be change on different instances of the platform,
like for example, where develop the code or in production or for those values
that can not be in a flat file because it contain sensible information, they will
store on database and only the admin user will have access to view/modify.

To upload these parameters into Relecov Platform open a console terminal and inside
virtual environment execute:

```
python manage.py loaddata conf/upload_tables.json
```



### iSkyLIMS settings

Define the iSkyLIMS settings by selecting admin page **(iskylims_url/admin)** using the admin user credentials to login.

Navigate on the left side and click on the **Config Settings** table.

Then on the right side you will see the parameter list that you can modify and
change according to your configuration.

The following figure is displayed.

![relecov-platform iSkyLIMS settings](img/admin_iSkyLIMS_settings.png)

As you can see there are 3 parameters related with iSkyLIMS:
- ISKYLIMS_SERVER.
- ISKYLIMS_USER.
- ISKYLIMS_PASSWORD

**ISKYLIMS_SERVER**. Contains the url where the iSkyLIMS is located. For example: www.iskylims.org

**ISKYLIMS_USER** / **ISKYLIMS_PASSWORD**. Contains the login credentials (userid and
password) that are defined on iSkyLIMS to send the REST API request.
