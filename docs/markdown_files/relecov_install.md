# RELECOV Installation

The RELECOV application is built using the Django framework.

## Prerequisites

Before installing RELECOV, ensure the following requirements are met:

- The application must be installed on a Linux server. It has been tested on Ubuntu 22.04, CentOS 7, and Red Hat 8.  
- Python 3.8.10 or higher must be installed.  
- A MySQL server must be installed locally or accessible remotely.  
- A database named **`relecov_platform`** must be created.  
- A MySQL user with permissions to create, delete, and modify tables and indexes must be configured.  
- An Apache server must be running.  
- An iSkyLIMS instance must be installed. Follow the instructions here: [iSkyLIMS GitHub](https://github.com/BU-ISCIII/iSkyLIMS#readme).  
- The Nextstrain application must be available.

An installation script is available to automate software setup and initial configuration.

You can find the script and full installation guide on GitHub: [Relecov-platform GitHub](https://github.com/BU-ISCIII/relecov-platform#readme).

## Settings

Certain configuration values may differ depending on whether the application is being set up for testing or production.

These configurable settings (e.g., server URLs) are stored in the database and can only be viewed or modified by the **`admin` user**.

During installation, the script will prompt you to create the credentials for the admin user.

Once installed:

1. Open your web browser and go to `localhost/admin` or `server_domain/admin`.

2. Log in with the admin credentials.

   ![admin-login](img/admin_login.png)

3. Scroll down the left menu and click on **Config settings** to view all customizable parameters.

> Do **NOT** change the **Configuration Name** values.  
> Modifying these names may cause the application to fail.

Some settings are populated with dummy values during installation. The next sections explain how to correctly update them.

---

### iSkyLIMS Settings

As previously noted, an iSkyLIMS instance must be available.

Three parameters must be configured:

- `ISKYLIMS_SERVER` — the URL of your iSkyLIMS instance (e.g., `https://www.iskylims.org`)
- `ISKYLIMS_USER` — the username used to authenticate with iSkyLIMS
- `ISKYLIMS_PASSWORD` — the corresponding password

---

### Nextstrain

Click on the `NEXTSTRAIN_URL` setting and replace the placeholder with the actual URL and port of your Nextstrain service (e.g., `http://localhost:8100`).

---

### Samba Folder

Set the path to the Samba-shared folder where metadata files will be saved when using the metadata form.

---

### Your Institution

Click on `SUBMITTING_INSTITUTION` and update the value with the full name of your institution.

---

### Other Settings

There are other optional parameters not explicitly covered here.  
We recommend keeping their default values, as they have been preconfigured for standard use.

```bash
python manage.py loaddata conf/upload_tables.json
```