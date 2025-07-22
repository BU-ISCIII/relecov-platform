# API schema

The Schema API defines and enforces the structure of data managed by Open Data for Industries.

A **schema** is a structure written in JSON format. It provides data type information for the fields in a data record.

At its core, a schema specifies whether a field is a string, integer, floating-point number, geopoint, or another supported data type.

By validating input request fields against the schema, the system ensures that only requests with allowed values and structures are accepted.

## Schema structure

Schemas are defined in JSON format and follow a standardized structure to ensure consistent identification within the Open Data for Industries service.

This API schema is based on the **OpenAPI Specification (OAS)** — a language-agnostic standard for HTTP APIs. OpenAPI allows both humans and machines to easily understand and interact with the service—without needing access to source code, documentation, or inspecting network traffic.

When correctly defined, the schema enables seamless integration with minimal implementation effort.

**Relecov follows the [OpenAPI 3.0 specification](https://swagger.io/specification/).**


## Schema operations

For accessing Relecov 2 APIs request are implemented.

| API Endpoint | Description                                  |
|--------------|----------------------------------------------|
| `POST`       | Create a new object in the Relecov database  |
| `PUT`        | Update an existing object in the database    |

### `POST` Requests

POST requests are used to:

- Create sample data using laboratory metadata. 
- Create bioinformatics data from analysis metadata.  
- Create variant data for analyses that have reached a consensus.  

### `PUT` Requests

PUT requests are used to:

- Update the state of a sample, allowing the system to track its progress through various processing stages.

Both `POST` and `PUT` requests require a **request body** formatted as an **Info object**, which is a JSON object with field names and corresponding values:

```
{
    "field_name" : value
}
```

## Data types

The API supports various data types as defined in the OpenAPI 3.0 specification, including:

- `integer`
- `date`
- `string`
- `geopoint`
- and others

> **Important:** When sending data to Relecov, all values must be provided as **strings**, regardless of their actual data type.

### Date Format

Date fields must follow the format:  
**`YYYY-MM-DD`**

#### Example:

```json
"sample_collection_date": "2020-12-20"