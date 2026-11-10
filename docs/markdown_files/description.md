# Description

## RELECOV: Spanish Network for Genomic Surveillance of SARS-CoV-2
The replication process of the SARS-CoV-2 virus, like that of other viruses, involves changes in its genome through mutations. Thanks to genomic sequencing, it has been possible to observe the evolutionary adaptation and diversification of SARS-CoV-2 worldwide throughout the pandemic. Surveillance of these changes has enabled monitoring of their emergence and impact, especially those that could be associated with increased severity or lethality, escape neutralizing antibodies generated after prior infection or vaccination, evade detection by diagnostic methods, or resist potential treatments. The appearance of variants bearing such changes could have significant epidemiological consequences and pose a public health problem.

For this reason, on January 19 the European Commission published a statement urging countries to increase their sequencing rate by requesting sequencing of at least 5 %—and preferably 10 %—of positive COVID-19 test results, minimize delays in reporting, and ensure that data are shared to allow for meaningful comparisons. In response, the Genomic Sequencing Laboratory Network (RELECOV) was established. RELECOV aims to meet Spain’s national SARS-CoV-2 sequencing needs.

Inmaculada Casas. Head of Respiratory and Influenza Unit, WHO National Influenza Center-Madrid.

Coordinated by the Reference Laboratory for Respiratory Viruses of the National Microbiology Center (Carlos III Health Institute), this network reports cases to the ECDC and WHO. Participants have been designated by the various Autonomous Communities—each region and the two autonomous cities are represented. Depending on their regional decisions, laboratories or sequencing consortia may join the network in various capacities. Early generation of sequences and pooling of genomic data are key tools for viral surveillance and preparation for future public health alerts.

More info can be found [here](https://relecov.isciii.es/news-reports/).

## Platform Overview

The RELECOV platform consists of several components that work together to collect, store, and share SARS-CoV-2 genomic data. It ingests FASTQ files along with their metadata, which are processed through multiple steps:

1. Metadata validation and upload to a central database  
2. Standardized bioinformatic analysis of raw data  
3. Validation of bioinformatic metadata and upload to the database  
4. Sharing of data with public repositories  
5. Data visualization and analysis  
6. Controlled access to data following FAIR principles

![overview-platform](img/overview_platform.png)

The platform relies on two main software components: the RELECOV website and database, and a set of helper tools called **relecov-tools**.

## RELECOV Platform Website

The website stores all processed data and metadata, and enables the visualization of various metrics and statistics, including a national installation of Nextstrain. It also includes an intranet for sample tracking by participating laboratories, and a REST API that provides controlled data access for network members.

## relecov-tools

**relecov-tools** is a Python package that provides helper functions for data management within the project. Read more [here](../relecov_tools.md).