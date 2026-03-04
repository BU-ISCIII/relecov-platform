# Generic imports
import inspect
from datetime import datetime
from collections import defaultdict

# Local imports
import core.models
import dashboard.models
import dashboard.utils.generic_process_data


def get_top_level_function_names(module):
    # Get a list of all functions in the module
    functions = inspect.getmembers(module, inspect.isfunction)
    # Extract only the top-level methods, excluding inner methods
    return [
        func[0]
        for func in functions
        if func[1].__module__ == dashboard.utils.generic_process_data.__name__
    ]


def remove_older_graphic_jsons(graphic_name, date):
    """Remove graphic jsons with creation date strictly older than given (not equal to)

    Args:
        graphic_name (str): Name of the graphic json to delete
        date (datetime): Date from which graphic jsons will be deleted
    """
    dashboard.models.GraphicJsonFile.objects.filter(
        graphic_name__exact=graphic_name, creation_date__lt=date
    ).delete()
    return


def update_graphic_json_data():
    """This function is called from crontab to update graphic json data.
    It also removes all the previous graphic jsons except for the last.
    In the end, there should remain 2 graphic jsons for each category,
    the last one and the newly created one.

    NOTE: this crontab should be updated if any new graphic json is
    included in the platform by including a method call along with the rest
    """
    names_and_dates = dashboard.models.GraphicJsonFile.objects.values(
        "graphic_name", "creation_date"
    )
    grouped_jsons = defaultdict(list)
    for item in names_and_dates:
        grouped_jsons[item["graphic_name"]].append(item["creation_date"])
    for graphic_name, dates in grouped_jsons.items():
        last_date = max(dates)
        # Keep only the last graphic json
        remove_older_graphic_jsons(graphic_name, last_date)

    # Start updating all graphic jsons
    print("Starting graphic jsons update...")
    print("Start timestamp: ", datetime.today().strftime("%Y-%m-%d %H:%M:%S"))
    print("Running pre_proc_calculation_date()")
    dashboard.utils.generic_process_data.pre_proc_calculation_date()
    print("Running pre_proc_variant_graphic()")
    dashboard.utils.generic_process_data.pre_proc_variant_graphic()
    print("Running pre_proc_specimen_source_pcr_1()")
    dashboard.utils.generic_process_data.pre_proc_specimen_source_pcr_1()
    print("Running pre_proc_extraction_protocol_pcr_1()")
    dashboard.utils.generic_process_data.pre_proc_extraction_protocol_pcr_1()
    print("Running pre_proc_library_kit_pcr_1()")
    dashboard.utils.generic_process_data.pre_proc_library_kit_pcr_1()
    print("Running pre_proc_based_pairs_sequenced()")
    dashboard.utils.generic_process_data.pre_proc_based_pairs_sequenced()
    print("Running pre_proc_depth_variants()")
    dashboard.utils.generic_process_data.pre_proc_depth_variants()
    print("Running pre_proc_depth_sample_run()")
    dashboard.utils.generic_process_data.pre_proc_depth_sample_run()
    print("Running pre_proc_samples_received_map()")
    dashboard.utils.generic_process_data.pre_proc_samples_received_map()
    print("Running pre_proc_host_info()")
    dashboard.utils.generic_process_data.pre_proc_host_info()
    print("Running pre_proc_samples_per_date_all_lab()")
    dashboard.utils.generic_process_data.pre_proc_samples_per_date_all_lab()
    print("Running pre_proc_samples_per_date_all_lab(detailed=True)")
    dashboard.utils.generic_process_data.pre_proc_samples_per_date_all_lab(
        detailed=True
    )
    print("Running pre_proc_samples_received_per_lab()")
    dashboard.utils.generic_process_data.pre_proc_samples_received_per_lab()
    print("Running pre_proc_samples_received_per_ccaa()")
    dashboard.utils.generic_process_data.pre_proc_samples_received_per_ccaa()
    print("Running pre_proc_intranet_gisaid_data")
    dashboard.utils.generic_process_data.pre_proc_intranet_gisaid_data()
    print("Running pre_proc_intranet_ena_data()")
    dashboard.utils.generic_process_data.pre_proc_intranet_ena_data()
    print("Running pre_proc_search_samples_summary()")
    dashboard.utils.generic_process_data.pre_proc_search_samples_summary()
    print("Running pre_proc_bioinfo_fields_util()")
    dashboard.utils.generic_process_data.pre_proc_bioinfo_fields_util()
    uniq_chrom_id_list = [
        x["chromosomeID"]
        for x in core.models.Gene.objects.values("chromosomeID").distinct()
    ]
    print(f"List of extracted unique chromosomes: {uniq_chrom_id_list}")
    print("Running pre_proc_variations_per_lineage() for each chromosome")
    for chromosome in uniq_chrom_id_list:
        dashboard.utils.generic_process_data.pre_proc_variations_per_lineage(
            chromosome=chromosome
        )
    print("Graphic jsons update finished")
    print("End timestamp: ", datetime.today().strftime("%Y-%m-%d %H:%M:%S"))
