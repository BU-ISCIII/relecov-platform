# Upload Samples to GISAID

**GISAID** (Global Initiative on Sharing All Influenza Data) is an international platform focused on sharing genomic data related to influenza and other respiratory viruses, including **SARS-CoV-2**.  
Its primary goal is to enhance global surveillance and response efforts by enabling timely sharing of sequences and associated metadata.

During the COVID-19 pandemic, GISAID played a crucial role in the global exchange of SARS-CoV-2 genomic data. It remains a vital resource, offering tools such as the [CoVsurver mutation analysis app](https://gisaid.org/database-features/covsurver-mutations-app/).

## How to Submit Data to GISAID

To upload your sequences to the GISAID database:

1. **Register for a GISAID account** at [gisaid.org](https://gisaid.org).
2. For **programmatic submissions**, you will need an **API token** associated with your account.

GISAID provides several submission methods, including graphical tools and command-line interfaces. More information is available on their [submission tools page](https://gisaid.org/database-features/submission-tool-cli4/).

## Semi-Automated Submission with Relecov-tools

The [**relecov-tools**](https://github.com/BU-ISCIII/relecov-tools?tab=readme-ov-file#upload-to-gisaid) package includes a module to simplify sample submission to GISAID.

To use it:

1. Install the `relecov-tools` package.
2. Follow the instructions provided in the repository.

This tool facilitates semi-automated uploads, helping streamline your data sharing process with GISAID.