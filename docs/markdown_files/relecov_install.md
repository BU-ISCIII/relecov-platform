# Relecov Installation

The Relecov application uses Django as the main framework.

The installation procedure assumes that the following requirements are fulfilled:

-  The Relecov application must be installed on a Linux server. Tested on Ubuntu 22.04, CentOS 7, and Red Hat 8.  
-  Python 3.8.10 or higher must be already installed.  
-  A MySQL server must be installed on the server or accessible remotely.  
-  A database named **"relecov_platform"** must be created.  
-  A user must be configured to access this database with the appropriate permissions to create, delete, and modify tables and indexes.  
-  An Apache server must be running on the server.  
-  iSkyLIMS must be installed. Follow the installation guide on GitHub: [iSkyLIMS](https://github.com/BU-ISCIII/iSkyLIMS#readme).  
-  The Nextstrain application must be available.

For your convenience, an installation script has been created to perform the software installation and initial configuration.

The installation procedure, as well as the script, is available on GitHub: [Relecov-platform](https://github.com/BU-ISCIII/relecov-platform#readme)

## Settings

There are some settings that may vary across different instances of the platform.  
For example, when installing the application in a testing environment, the configuration may differ from that of the production environment.

We have also defined some settings that can change, such as server URLs, without impacting the installation process.

These settings are stored in the database and can be viewed or modified only by the admin user.

During the installation, the script will prompt you to define the credentials for the admin user.

Open your preferred browser and navigate to `localhost/admin` or `server_domain/admin` to access the Django admin interface.

![admin-login](img/admin_login.png)

After logging in, scroll down on the left side and click on **"Config settings"** to view the parameters whose values you may need to adjust for your installation.

> **WARNING**  
>  
> **DO NOT CHANGE** the CONFIGURATION NAME.
> Changing these names will cause the application to malfunction.

Some default settings are populated with dummy values during installation.

In the following chapters, we provide guidance on how to set the correct values for your installation.

### iSkyLIMS settings

As mentioned in the requirements, an iSkyLIMS instance must be installed.

There are three parameters that must be set:

- `ISKYLIMS_SERVER`  
- `ISKYLIMS_USER`  
- `ISKYLIMS_PASSWORD`

**ISKYLIMS_SERVER**: Contains the URL where the iSkyLIMS instance is located. Example: `www.iskylims.org`

**ISKYLIMS_USER** / **ISKYLIMS_PASSWORD**: Contain the login credentials (username and password) defined previously in iSkyLIMS.

### Nextstrain

Click on **NEXTSTRAIN_URL** and update the configuration value with the URL and port of your Nextstrain application.

### Samba folder

Define the folder where metadata files will be stored when using the metadata form page.

### Your institution

Click on **SUBMITTING_INSTITUTION** and replace the dummy value with the name of your institution.

### Remaining values

There are additional parameters not described above.  
We recommend keeping their default values as they are already properly configured.

```bash
python manage.py loaddata conf/upload_tables.json
```