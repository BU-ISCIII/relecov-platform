# Metadata Handbook

## Metadata scheme creation

The main purpose of RELECOV platform is to store and make accessible SARS-CoV-2 genomic data along with its metadata. As its focus is on genomic data, it gathers metadata related with sample processing, sequencing and bioinformatic analysis; leaving clinic and specific epidemiological data to be collected by the national authorities and stored in the epidemiological national database ([Sivies](https://sivies.isciii.es/Web/Seguridad/Login.aspx?ReturnUrl=%2f)). RELECOV aims to be able to intercomunicate with SiVies in the future.

Therefore, already available data specifications for sars-cov-2 databases we have been used to create a custom complete relecov specification:

- Ph4age SARS-CoV-2 specification: [link](https://github.com/pha4ge/SARS-CoV-2-Contextual-Data-Specification)
- ENA required Metadata: [link](https://www.ebi.ac.uk/ena/browser/view/ERC000033)
- GISAID required metadata: [link](https://gisaid.org/)

Collected fields were evaluated and mapped against each other, while being annoted with the appropiate ontology term whenever possible ([GENEPIO](https://genepio.org/)). This mapping can be consulted [here](https://docs.google.com/spreadsheets/d/1Qehkcml1WFwE9n2rBiIoAmlILwzPT4hb/edit?usp=sharing&ouid=114088100290741425598&rtpof=true&sd=true).

## JSON schema
Based on the work in the previous section, a common metadata schema to be collected and stored in the platform database was agreed among the project partners. The schema has been decribed using a the [json schema specification](https://json-schema.org/specification.html) and can be checked [here](https://github.com/BU-ISCIII/relecov-tools/blob/develop/relecov_tools/schema/relecov_schema.json)

Ph4age classification fields have been extended according to their nature:
1. Sample collection and processing
2. Database Identifiers
3. Host information
4. Sequencing
5. Files info
6. Bioinformatic Analysis fields
7. Lineage fields
8. Pathogen diagnostic testing
9. Public databases

An excel file has been generated including the fields belonging to the labs to facilitate its collection and upload to the platform. [See next section](metadata_lab_excel.md)
