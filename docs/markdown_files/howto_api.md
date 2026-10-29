# How to Use the Relecov Platform API

There are three ways to send a request using the Relecov API:

- Graphical interface using Swagger  
- update-db module from Relecov-tools  
- Terminal console using curl or a similar tool

For any of these methods, the user must provide authentication credentials to upload information to the Relecov Platform.

## Graphical Interface Using Swagger

The Swagger application is already integrated with the Relecov Platform.  
You can access it by typing the following URL in your browser:

http://your_relecov_server/swagger

On the Swagger page, you'll see an Authorize button at the top right corner:

![swagger](img/swagger_main.png)

Click the Authorize button to enter your user credentials. Type your username and password, then click Authorize.

At this point, the credentials are stored in your local browser for use during the session. Note that no validation is performed on the server side until you send a request.

> **Note:** apiKey authentication is not implemented yet. This method is planned for a future release.

### Create Sample

The first POST request you should make is **createSampleData**. Click the down arrow to expand additional information for this request.

There are two main sections:

- Request body  
- Responses

In the Request body, you’ll see an example in JSON format. Each line shows a field name on the left and a value on the right.

Below the example, the Responses section displays possible response codes.

To send the createSampleData request, click the **Try it out** button.

This action enables the input field with a white background where you can modify the example values. Once you've entered the appropriate data, click the **Execute** button.

If the values are valid, you will receive a successful response.

### Create Bioinfo Data

After the sample is defined in the database, you can add more information using the **createBioinfoData** request.

Click the down arrow to view the example request and possible responses.

Follow the same procedure: click **Try it out**, edit the example data, and click **Execute**.

### Create Variant Data

To add variant information for a sample, use the **createVariantData** request.

This request differs slightly from the previous ones because the `variants` field is a list of dictionaries.

The example shows two variants. Repeat the structure as many times as necessary to include all variants found in your sample.

### Update Sample State

This request is used to update the state of a sample. A state represents an action performed on the sample. For example, to indicate that a sample has been uploaded to ENA, use this PUT request with the state set to "Ena".

## Using relecov-tools

The `relecov-tools` Python package is designed to simplify the process of collecting metadata from laboratories or hospitals and uploading it to the Relecov Platform.

To upload data, use the `update-db` option when running the `relecov-tools` command.

For more details, visit the GitHub repository: https://github.com/BU-ISCIII/relecov-tools.

## Using Terminal (curl or similar)

Open a terminal and define the request by specifying the URL and headers such as content type. Include the appropriate fields and values in the request body.

### Example for sending the request using curl command
Below are examples you can use to send requests to the Relecov platform:

#### Example for Create Sample

```
curl -X 'POST' \
  'http://<your relecov url server>/api/createSampleData' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -H 'X-CSRFTOKEN: H5Mt8YOYlg0uxjv3LlhTSFtVbjOwvKydHCGydww5soT5dAezQN9e5F3uKkIjHUko' \
  -d '{

   }'

```
Inside the `-d` block, include the sample data. Use as template the example that was shown before in the Swagger chapter.

#### Example for Bioinfo Data

```
curl -X 'POST' \
  'http://<your relecov url server>/api/createBioinfoData' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -H 'X-CSRFTOKEN: QwHvCeQvU9DPTCT679DkG6dBrTtDP1RuQ3BAHMyC1hwqzTCCcBvFT6Na0Unq1bDF' \
  -d '{
    
   }'

```

#### Example for Variant Sample Data

Use this information to build your request. Fill in the `variants` field using the same structure as described above.

```
curl -X 'POST' \
  'http://<your relecov url server>/api/createVariantData' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -H 'X-CSRFTOKEN: QwHvCeQvU9DPTCT679DkG6dBrTtDP1RuQ3BAHMyC1hwqzTCCcBvFT6Na0Unq1bDF' \
  -d '{
  "sample_name": "your sample",
  "variants": [

   ],
   }'
   
``` 

#### Example for Update State Sample
Using this example, replace the `sample_name` and `state` fields with your settings:

```
curl -X 'PUT' \
  'http://<your relecov url server>/api/updateState' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -H 'X-CSRFTOKEN: QwHvCeQvU9DPTCT679DkG6dBrTtDP1RuQ3BAHMyC1hwqzTCCcBvFT6Na0Unq1bDF' \
  -d '{
  "sample_name": "your sample",
  "state": "state value"
}'
```
