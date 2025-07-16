# Metadata Handbook

## Metadata scheme creation

The main purpose of the RELECOV platform is to store and make accessible SARS-CoV-2 genomic data along with its metadata. Since its focus is on genomic data, it gathers metadata related to sample processing, sequencing, and bioinformatic analysis, leaving clinical and specific epidemiological data to be collected by national authorities and stored in the national epidemiological database ([SiVies](https://sivies.isciii.es/Web/Seguridad/Login.aspx?ReturnUrl=%2f)). RELECOV aims to intercommunicate with SiVies in the future.

We reviewed existing data specifications for SARS-CoV-2 databases and used them to create a complete custom RELECOV specification:

- PHA4GE SARS-CoV-2 Contextual Data Specification: [link](https://github.com/pha4ge/SARS-CoV-2-Contextual-Data-Specification)
- ENA required metadata: [link](https://www.ebi.ac.uk/ena/browser/view/ERC000033)
- GISAID required metadata: [link](https://gisaid.org/)

Collected fields were evaluated and mapped against each other, and annotated with the appropriate ontology term whenever possible ([GENEPIO](https://genepio.org/)). You can consult this mapping [here](https://docs.google.com/spreadsheets/d/1Qehkcml1WFwE9n2rBiIoAmlILwzPT4hb/edit?usp=sharing&ouid=114088100290741425598&rtpof=true&sd=true).

## JSON Schema

Based on the work in the previous section, the project partners agreed on a common metadata schema to be collected and stored in the platform database. The schema is described using the [JSON Schema specification](https://json-schema.org/specification.html) and can be viewed [here](https://github.com/BU-ISCIII/relecov-tools/blob/develop/relecov_tools/schema/relecov_schema.json).

The schema properties have been classified according to their nature, which will impact in which database they will be sotred:

Stored in iSkyLIMS:

1. Sample collection and processing
2. Database identifiers
3. Host information
4. Sequencing
5. Files info
6. Pathogen diagnostic testing

Stored in RELECOV-platform:

1. Bioinformatic Analysis fields
2. Bioinformatic Variants
3. Bioinformatics and QC metrics fields
4. Lineage fields
5. Clade fields
6. Public databases
7. Submission ENA

An Excel file has been generated, including the metadata fields for each lab to facilitate data collection and upload to the platform. [See next section](../metadata_lab_excel.md)
