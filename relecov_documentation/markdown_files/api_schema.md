# API schema

The Schema API provides mechanisms to define and enforce structure to the data 
that is managed by Open Data for Industries.


A schema is a structure, which is defined in JSON format. It provides data 
type information for the data record fields.

In a simple definition, the schema defines whether a field in the record is a 
string, integer, floating point, geopoint, or other data types.

Input request fields can be validated, against the schema, allowing only requests which contain the values that are allowed in the schema.

## Schema structure

Schemas are defined in JSON format. These definitions follow a structure to standardize the identification of the schemas in the Open Data for Industries service.

The API schema is based in a structure that is defined in the OpenAPI 
Specification (OAS) standards.  Language-agnostic interface to HTTP APIs 
which allows both humans and computers to discover and 
understand the capabilities of the service without access to source code, 
documentation, or through network traffic inspection. 

When properly defined, a consumer can understand and interact with the remote service with a minimal amount of implementation logic.  

Relecov uses is according to the [OpenAPI 3.0 specification](https://swagger.io/specification/).


## Schema operations

For accessing Relecov 2 APIs request are implemented.

| API endpoint  | Description |
| ------------- | ----------- |
| POST          | Create and object in relecov database |
| PUT           | Update and object that is already defined in database |


We are using POST request for:

- Create Sample data using Metadata laboratory
- Create Bioinfo data from Analysis Metadata
- Create Variant data for those analysis that reached a consensus.

PUT request used for:

- Update state of sample. To track the actions that are done for a sample.


POST and PUT requests contain a "request body" that is defined as **Info object**. This object is written in a JSON format where field names and values are defined.


```
{
    "field_name" : value
}

```

## Data types

Different data types is allowed in API 3.0, like "integer", "date", "string", 
etc. But when sending a request to relecov you must set them as "string" 
format data. 

In case of date fields they must be sent following this format "YYYY-MM-DD" per example **2020-12-20**.