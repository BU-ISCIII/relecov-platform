# Metadata Handbook

## Metadata Schema Creation

The primary goal of the RELECOV platform is to store and provide access to SARS-CoV-2 genomic data along with its associated metadata. Since the focus is on genomic data, the platform collects metadata related to sample processing, sequencing, and bioinformatic analysis. Clinical and specific epidemiological data are gathered separately by national health authorities and stored in the national epidemiological database, [SiVies](https://sivies.isciii.es/Web/Seguridad/Login.aspx?ReturnUrl=%2f). RELECOV aims to interoperate with SiVies in the future.

To define a comprehensive metadata structure, we reviewed existing data specifications used in SARS-CoV-2 databases and used them to develop a custom RELECOV specification:

- [PHA4GE SARS-CoV-2 Contextual Data Specification](https://github.com/pha4ge/SARS-CoV-2-Contextual-Data-Specification)  
- [ENA required metadata](https://www.ebi.ac.uk/ena/browser/view/ERC000033)  
- [GISAID required metadata](https://gisaid.org/)

The collected metadata fields were analyzed, cross-referenced, and annotated with appropriate ontology terms whenever possible, such as those from [GENEPIO](https://genepio.org/). You can view the full mapping [here](https://docs.google.com/spreadsheets/d/1Qehkcml1WFwE9n2rBiIoAmlILwzPT4hb/edit?usp=sharing&ouid=114088100290741425598&rtpof=true&sd=true).

## JSON Schema

Based on the work described above, project partners agreed on a common metadata schema to be collected and stored in the platform's database. This schema follows the [JSON Schema specification](https://json-schema.org/specification.html) and is available [here](https://github.com/BU-ISCIII/relecov-tools/blob/develop/relecov_tools/schema/relecov_schema.json).

The schema's properties are categorized by their nature, which determines where they are stored:

**Stored in iSkyLIMS:**

1. Sample collection and processing  
2. Database identifiers  
3. Host information  
4. Sequencing  
5. File information  
6. Pathogen diagnostic testing  

**Stored in the RELECOV platform:**

1. Bioinformatic analysis fields  
2. Bioinformatic variants  
3. Bioinformatics and QC metrics fields  
4. Lineage fields  
5. Clade fields  
6. Database Identifiers 
7. Files info
8. Host information
9. Pathogen diagnostic testing
10. Public databases
11. Sample collection and processing
12. Sequencing
13. Submission ENA

To facilitate data collection and uploading to the platform, an Excel template containing all required metadata fields has been prepared for each laboratory. Please 
[check the next section](../metadata_lab_excel.md).
