# Upload Metadata Lab

There are three different methods you can use to upload sample metadata:

1. Filling out the Metadata Lab form
2. Uploading a Metadata Excel file
3. Using the SFTP server

Below we describe the different options and their requirements so you can choose the method that best suits your needs.

### 1. Filling out the Metadata Lab form

With this option, you don’t need to prepare any file in advance.  
Simply fill in the form, which will guide you step by step.

### 2. Uploading a Metadata Excel file

In this case, you need to fill in the Metadata Lab Excel file beforehand.

### 3. Using the SFTP Server

This option is not available directly through the Relecov interface.  
You must upload the completed Metadata Excel file to the SFTP server.  
Instructions for this process are provided in [How to fill metadata lab excel](../metadata_lab_excel.md).

---

**If you choose option 1 or 2**, click the **Upload Metadata** link from the left menu to open the upload page.

Since some of the data is stored in iSkyLIMS, the system will check the connection to iSkyLIMS.  
If it is not reachable, an error message will be displayed, and you won’t be able to continue until the issue is resolved.

![error_iskylims_not_available](img/error_iskylims_not_available.png)

On the Metadata Form page, you will see the logged-in user ID and the laboratory they are associated with.  
Please verify this information, as it will be attached to the uploaded metadata.

## Metadata Lab Form

When the page loads, this method is shown by default:

![form_metadata_lab](img/form_metadata_lab.png)

There are several required fields to complete.  
To avoid duplicating information, metadata is split into two groups:
- Fields that vary for each sample
- Fields that are common to all samples being uploaded

Based on this, the form is divided into two pages.

The first page is a spreadsheet-style form where you can:
- Type directly into each cell
- Copy and paste data from an existing Excel file

The form includes three types of inputs:
- **Text**: Type the content directly.
- **Date**: Click the cell to select from a calendar.
- **Select**: Click to choose from a dropdown menu.

> If you're unsure how to fill in a field, refer to [How to fill metadata lab excel](../metadata_lab_excel.md).

After completing the form, click the **Submit** button.

The second page will appear, showing fields that apply to **all** samples entered on the previous page.

Once this is filled, click **Submit** again to confirm.

A success page will appear, confirming that your metadata has been successfully stored for validation.

> **Note**: You are not required to complete the second page immediately.  
You can return to it at any time — the page will be shown again the next time you access the Metadata Lab form.

> **Note**: Only the user who entered the data on the first page can retrieve and edit that information later.

---

## Upload Metadata Excel File

The second option is to upload a filled-in Metadata Lab Excel file.  
Once your file is ready, select the **Upload file** tab in the Metadata form.

![form_metadata_upload_file](img/form_metadata_upload_file.png)

Attach the file and click **Submit**.

A confirmation page will be shown once your data has been successfully stored for validation.