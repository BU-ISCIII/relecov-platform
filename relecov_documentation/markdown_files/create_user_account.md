# How to create an user account

### <red>The next steps are only for administrators.</red>

Contact the relecov-platform application administrator to provide you with a username and password.

#### **First step**

First of all we must create a superuser, which will be the administrator (admin).
We will do this through the terminal using the command:

> `$ python manage.py createsuperuser`

  We will enter the required information:
- Username.
- Email address. 
- Password.

After this step we will have defined the administrator of the relecov-platform application.

#### **Second step**

We must navigate to our website, for example http://relecov-platform.isciiides.es 
then We add /admin at the end of the URL, so then We will see the next URL: http://relecov-platform.isciiides.es/admin.

Django will show us the administration panel of the application.

![relecov-platform admin main page](../../static/relecov_documentation/img/admin_panel_main.png)

In the left panel we will click on Users

![relecov-platform admin add user 1](../../static/relecov_documentation/img/admin_panel_add_user1.png)


In the central part of the screen, a table will be displayed showing us all the users registered in the application, 
at the moment only the administrator, recently created in the previous step.
To add a new user we will click on the ADD USER button.

![relecov-platform admin add user 2](../../static/relecov_documentation/img/admin_panel_add_user2.png)

Fill username and password fields correctly and click on SAVE button.

![relecov-platform admin add user 3](../../static/relecov_documentation/img/admin_panel_add_user3.png)

After clicking on the SAVE button, we will see another form where we can enter more detailed information about the user, in addition to managing the permissions that the user will have.

**Personal info:**
   -  First name
   -  Last name
   -  Email address
**Permissions:**
  - Active:  *Designates whether this user should be treated as active*
  - Staff status: *Designates whether the user can log into this admin site*
  - Superuser status: *Designates that this user has all permissions without explicitly assigning them.*
  - Add to groups
  - User permissions