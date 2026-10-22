# Nextstrain Installation

The Nextstrain application is configured as a service on your server.

There are two main steps:

1. Install the Nextstrain software  
2. Create the service on your server

> **Note:** Installing Nextstrain requires `sudo` privileges, as it will be installed under `/opt`, and service creation also requires root access.

---

The instructions below assume that Nextstrain will be installed on the **same server** as the `relecov-platform`.

If you plan to install Nextstrain on a **different server**, the same procedure applies. You just need to **copy the service configuration file** from the `relecov-platform` server to the new machine.

---

## Install Nextstrain

First, create the installation directory and download the Nextstrain installer:
```
sudo mkdir -p /opt/nextstrain
cd /opt/nextstrain
sudo curl -fsSL --proto '=https' https://nextstrain.org/cli/installer/linux > nexstrain_installer_$(date "+%Y%m%d").sh
```
Set the NEXTSTRAIN_HOME environment variable and run the installer:
```
export NEXTSTRAIN_HOME=/opt/nextstrain
sudo bash nexstrain_installer_$(date "+%Y%m%d").sh
```

Set Conda as the default runtime environment (this installs the Nextstrain Conda environment using micromamba):
```
sudo /opt/nextstrain/cli-standalone/nextstrain setup --set-default conda
```

Next, copy the Auspice dataset to the appropriate folder.
This dataset includes the data that will be rendered in the Nextstrain app. You can generate it using the [nexstrain_relecov workflow](https://github.com/BU-ISCIII/nexstrain_relecov)
```
mkdir -p /opt/nextstrain/dataset/sars-cov-2
cp -r /path/to/auspice /opt/nextstrain/dataset/sars-cov-2
```

## Create Nextstrain service

The service configuration file is located in the **conf** directory of the relecov-platform.
If you change the installation folder from `/opt` to a different location, replace 
`/opt/` for your installation folder.
Copy the service file to `/etc/systemd/system`
```
sudo cp /opt/relecov-platform/conf/nextstrain.service /etc/systemd/system
```
By default, the service listens on port 8100. If you need to change this port, 
edit `/etc/systemd/system` and replace the default port number with your desired value, then save the file.

### Start Nexstrain service
To get the service up, you need to start the service:

```
sudo systemctl start nextstrain
```

Verify that it started successfully and that there are no errors.

## Define Nextstrain in Relecov-Platform

The final step in the Nextstrain setup is to configure its URL and port within the `relecov-platform`.

Open your favorite navigator and type the "localhost/admin" or the "server_domain/admin/ 
to connect with Django admin application.

![admin-login](img/admin_login.png)

After login, scroll down on the left side and click on **"Config settings"**.

Click on the **NEXTSTRAIN_URL** to change the existing dummy values.

Change the IP/URL and the port to the values that your Nextstrain application is using and
click the SAVE button to apply the changes.

## Check Nextstrain 

In your navigator, go now to the main page of relecov-platform.

Click on the "Nextstrain" button and check that a new tab is displayed with Nextstrain.

![nextstrain_box](img/nextstrain_box.png)
