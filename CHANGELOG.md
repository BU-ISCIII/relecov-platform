# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-05

First stable release of the RELECOV Platform. It covers everything built since the repository was created in March 2022: metadata handling, bioinformatics data ingestion, the REST API, the iSkyLIMS integration, the public and private dashboards, the user documentation, and a containerised production deployment that follows the BU-ISCIII deployment standard.

## Credits

- [Sara Monzón](https://github.com/saramonzon)
- [Sarai Varona](https://github.com/svarona)
- [Alejandro Bernabeu](https://github.com/aberdur)
- [Enrique Sapena](https://github.com/ESapenaVentura)
- [Víctor López](https://github.com/victor5lm))
- [Daniel Villares](https://github.com/Daniel-VM)
- [Luis Chapado](https://github.com/luissian)
- [Pablo Mata](https://github.com/Shettland)
- [Alejandra gonzalez](https://github.com/alejandra-gonzalezs)
- [Pablo Aja Macaya](https://github.com/Pablo-Aja-Macaya)
- [Luis](https://github.com/luisijavo)
- [Sergio Olmos Piñero](https://github.com/OPSergio)


### Added

#### Core platform and data model

- Django project `relecov_platform` with three applications: `core`
  (intranet, metadata, API), `dashboard` (surveillance visualisations) and
  `docs` (built-in user documentation).
- JSON schema management: upload, versioning, default-schema handling and
  `fill_mode` support. Lineage fields and public database fields are created
  from the schema. The RELECOV JSON schema 3.0.0 is bundled in `conf/`.
- Admin form to edit loaded schemas in place.
- Sample model with state tracking (`update_state`, partial state updates),
  error recording, batch samples and analysis many-to-many relations.
- Unique sample identification: `sample_fingerprint`, later standardised to
  `sample_unique_id` (unique and non-null), with a configurable custom prefix.
- `submitting_institution` and `collecting_institution_code_1` (`lab_code_1`)
  on samples, used to scope data per laboratory.
- Bioinformatics storage: `BioinfoAnalysisField`/`Value`, `LineageField`/`Value`,
  pre-processing tables and support for additional lineage classifications.
- Variant storage: GFF annotation upload, chromosome and organism annotation,
  `VariantInSample`, `VariantAnnotation`, effects and filters (long table).
- `FIELD_EMPTY_VALUES` setting, so "Not Provided", "Not Applicable
  [GENEPIO:0001619]", "Missing" and similar values are treated the same
  everywhere.
- Initial committed migrations for `core` and `dashboard`.

#### REST API

- REST API built on Django REST Framework, documented with OpenAPI through
  `drf-spectacular` (it replaced Swagger), with request and response examples.
- Endpoints to create samples, upload bioinformatics metadata and variant
  long tables, update sample state, create batch samples, and fetch sample
  project fields.
- `checkSampleExists` endpoint (previously `getSampleData`), with extra
  query parameters.
- Standardised API response format across core endpoints.
- Chunked variant uploads, with one atomic transaction per variant record,
  to limit memory use on large payloads.

#### iSkyLIMS integration

- REST integration with iSkyLIMS to retrieve laboratory, sample and
  ENA/GISAID submission data.
- Bulk requests to iSkyLIMS to speed up sample browser downloads.
- All iSkyLIMS lookups use the unique sample ID.

#### Intranet

- Login-protected intranet with a side menu shared across pages.
- Metadata form (JExcel-based) with dropdowns filled from the database, and
  metadata file upload.
- Laboratory contact data view and editing.
- Sample search and sample display views, including ENA and GISAID
  accessions, variant tables and per-sample graphs.
- Received samples view with maps and per-laboratory and per-region charts.
- Separate intranet views for the *collector* and *submitter* user groups,
  with a laboratory selector for users linked to several laboratories.
- Sample Browser:
  - Server-side DataTables.
  - Multi-select collecting institution filter, plus lineage and institution
    filters that update from the other filters.
  - Date range filter and a "clear filters" button.
  - Download buttons for the filtered table, surveillance data, aggregated
    surveillance data and variant data (CSV).
- Animated HTML progress bars and gauges that show how complete the
  bioinformatics fields are.

#### Dashboards

- Variants dashboard:
  - Lineages over time (later "variants over time") and Lineages VOC
    charts, grouped by collection date as ISO weeks.
  - Mutations in lineage needle plot, rewritten from scratch for speed and
    showing the number of samples.
  - Mutation heatmap, spike mutations table and 3D molecule view.
  - Choropleth maps of samples and lineages per autonomous community
    (Plotly/Mapbox, later Folium).
  - Samples received by region and by laboratory.
- Methodology dashboard:
  - Sample processing, sequencing, bioinformatics and host information
    (age, gender) sections.
  - Ridge plots and box plots that draw only outliers.
  - Ct value vs. sequenced base pairs, with a Ct cap at 40.
  - Read length charts with log scaling.
- Date range pickers on time-based graphs.
- Pre-computed graph data stored in the `GraphicJson` table and refreshed on
  a schedule (django-crontab, later supercronic in containers). The weekly
  and monthly jobs are split by cost.
- Unified colour palette, custom Plotly template, local fonts, and label
  truncation that keeps the full label in hover text.
- Responsive layouts for dashboards, sidebars, tables and gauges.
- Dashboards are publicly viewable, while protected Dash callbacks keep their
  restrictions.
- Nextstrain entry point on the home page.

#### Documentation

- Built-in documentation app that renders Markdown, with a sidebar that
  highlights the current page.
- User guides for the intranet, metadata handbook, laboratory Excel
  template, metadata upload, sample search, received samples, laboratory
  contact information, ENA and GISAID upload, the variants and methodology
  dashboards, relecov-tools, the API and API schema, user account creation,
  configuration, and installing and using Nextstrain.
- Platform overview, architecture description and updated infographics.
- Spanish installation manual (`LEAME.md`).
- Cookie consent banner and cookie policy page.

#### Deployment and operations

- `install.sh` for bare-metal installs on Ubuntu and CentOS/RedHat, with
  separate dependency and application steps, an upgrade mode,
  `--git_revision` to choose a branch or commit, and a migration check
  during upgrades.
- Apache configuration for Ubuntu and CentOS/RedHat.
- Container deployment with `Dockerfile`, `docker-compose.test.yml`,
  `docker-compose.prod.yml` and `container_install.sh`:
  - Gunicorn application server behind a containerised Apache reverse proxy
    that also serves iSkyLIMS and Nextstrain.
  - Nextstrain built during container installation, with datasets on a
    persistent volume and custom Mapbox configuration.
  - Production settings rendered from templates, with secrets preserved
    and protected settings bind-mounted.
  - SELinux-compatible volumes, HTTPS forwarded headers by default, and
    timezone data in the image.
  - Settings for Python 3.11 and the Europe/Madrid timezone.
- Alignment with the BU-ISCIII deployment standard (`project.json`,
  `deployment/`), including committed-migration validation, a migration
  plan check before `migrate`, a health endpoint and health checks, and
  per-service host directories, log policy and test databases.
- Test suite for `core` and `dashboard` with branch coverage reporting, and
  a GitHub Actions workflow for Python linting (black, flake8).

### Changed

- Apps renamed from `relecov_core`, `relecov_dashboard` and
  `relecov_documentation` to `core`, `dashboard` and `docs`. Dashboard
  utilities reorganised into `methodology/` and `variants/` modules.
- Default release branch renamed from `master` to `main`; development
  happens on `develop`.
- Samples are linked to institutions through `submitting_institution` and
  `lab_code_1` instead of free-text laboratory names. Queries use the
  collection date instead of the sequencing date.
- Field names updated to the newer schemas, for example `lineage_assignment`,
  sequence file fields, `bio_analysis_date`, and `host_age_years` and
  `host_age_months`.
- Front-end libraries upgraded: Bootstrap, Bootstrap Icons, Boxicons, Font
  Awesome, jQuery, Swiper and GLightbox.
- Dependencies upgraded to Django 5.2, Dash 3.1, django-plotly-dash 2.5,
  DRF 3.15 and pandas 2.2. Requires `relecov-tools>=1.8.0`.
- Dash initial state is stored in the session rather than the local memory
  cache, and Dash apps are registered at startup so they behave the same
  across Gunicorn workers.
- Faster pages: the methodology dashboard loads Plotly only once and caches
  its data, needle plot queries are quicker, bioinformatics upload is faster,
  the dashboard caches generate quicker, and lineage data loads only when a
  dashboard needs it.
- Interface wording clarified across the intranet and dashboards, for
  example "Assign Laboratory to User".
- Logo updated, and the login requirement removed from the home page.

### Fixed

- Errors on sample search: multiple matches, `KeyError`, searching by date or
  laboratory, and opening sample detail pages.
- ASCII codec errors with Nextstrain data.
- Wrong number of samples uploaded to ENA, crashes when ENA or GISAID data
  was missing, and partial GISAID data not being stored.
- Crashes when dates were incomplete, missing or in an invalid format, and
  when samples exist in iSkyLIMS but not in the platform (or the other way
  round).
- Dashboards failing or showing wrong results when there was no data,
  duplicated entries, or unstack/pivot errors, and samples counted more than
  once when they had several bioinformatics analyses.
- Wrong percentages for non-admin users, wrong "not provided" counts in host
  information, and unordered or missing ISO weeks.
- Region names in the Spain GeoJSON did not match standard labels (for
  example "Comunitat Valenciana").
- Broken documentation URLs, links to the external website, and the
  Nextstrain documentation paths.
- Laboratory contact form: placeholders, resubmitting after an error, and
  showing the updated data.
- Variant data upload: field typos, `variants` field parsing, and sample
  identifier lookup.
- Media path handling, permission errors on `MEDIA_ROOT`, and creation of the
  `documents/` folder during installation.
- Replaced the deprecated `pkg_resources` with `setuptools`.

### Removed

- Hackathon prototype templates, unused static files, legacy iSkyLIMS and
  InterOp install steps, Redis, and the deprecated `dash-renderer`.
- Inactive dashboard graph modules (moved to `notworking/`) and unused
  helper functions.
- Leftover `pdb` debugging statements.

### Security

- Dependencies upgraded to fix known vulnerabilities.
- Production settings and secrets are kept out of version control.
- Containers run cron jobs as a non-root user (supercronic).

[1.0.0]: https://github.com/BU-ISCIII/relecov-platform/releases/tag/v1.0.0
