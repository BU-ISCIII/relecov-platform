# Sample Search

To retrieve information about the samples stored in Relecov, a search form has been provided.

The **Sample Search** option is available in the Intranet area by selecting **Samples Search** from the left-side menu.

There are two different views depending on the role of the user currently logged in.

If the user has the **Relecov Manager** role, the following page is displayed:

![form_sample_search_manager](img/form_sample_search_manager.png)

You can filter by:
- **Sample State**: Every time an action is performed on a sample, a new state is added. For example, if a sample undergoes bioinformatic analysis, a corresponding analysis state is added.
- **Search by Name**: Use this to limit your search to a specific sample.
- **Sample defined date**: The date the sample was stored in Relecov.
- **Search by Laboratory**: Managers can search across all laboratories or limit the search to a specific one.

For users with **other roles**, a similar page is shown, but the search is restricted to samples uploaded by their own laboratory. These users cannot view or search for samples from other laboratories.

![form_sample_search](img/form_sample_search.png)

As shown in the heading, the search is limited to your laboratory.

When filling in the form, all filters are combined using **AND** logic. This means the results will match **all** selected criteria (e.g., state **and** date).

## Displaying Sample Search Results

There are two possible outcomes after submitting a search:

- Multiple samples match the criteria.
- Only one sample matches the criteria.

### Displaying Multiple Samples

![display_many_samples](img/display_many_samples.png)

If multiple samples match your query, a paginated table will be shown.  
You can click **Next** to view more results, or use the **Search** field to narrow them down.

Once you've found the correct sample, click on the sample link to view its detailed information.

### Displaying a Single Sample

If only one sample matches your query — or if you've clicked a sample link — the sample detail page is shown.

At the top, you’ll see several tabs with categorized information.

![display_sample_basic_1](img/display_sample_basic_1.png)

The number of tabs depends on the available data for the selected sample.  
If a tab is not visible, that means there is no data for that section.

The **Basic Data** tab opens by default. It includes:
- The various names assigned to the sample (e.g., laboratory name, microbiology ID, sequencing name).
- A history of actions performed on the sample, such as:
  - When it was stored in Relecov
  - Uploaded to GISAID
  - Metadata entry for bioinformatics
  - Variant analysis completion

A table at the bottom displays information related to the FASTQ file:

![display_sample_basic_2](img/display_sample_basic_2.png)

### Public Databases Tab

This tab contains information about the sample’s status in public databases such as GISAID and ENA.

In the following example, the sample has been uploaded to GISAID, but no information has yet been retrieved from ENA.

![display_sample_public](img/display_sample_public.png)

### Lab Data Tab

This section contains information provided in the lab metadata.

It is divided into two tables:
- **Metadata Lab Information**: includes the date the sample was recorded and collected.

  ![display_sample_lab_1](img/display_sample_lab_1.png)

- **Relecov project data**: includes additional metadata from the lab file.

  ![display_sample_lab_2](img/display_sample_lab_2.png)

You can browse additional pages using the **Next** button or search for specific parameters using the **Search** field.

### Analysis Tab

![display_sample_bio](img/display_sample_bio.png)

This tab shows data collected during bioinformatic analysis.  
You can browse or search within the table.

### Lineage Tab

Displays the lineage information of the sample.

![display_sample_analysis](img/display_sample_analysis.png)

### Variant Tab

Shows variant positions detected in the sample.

![display_sample_variant](img/display_sample_variant.png)

### Graph Tab

Displays graphical representations of the sample’s data.

![display_sample_graphic](img/display_sample_graphic.png)