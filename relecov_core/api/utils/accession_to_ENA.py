from datetime import datetime


def date_converter(received_date):
    """
    This function converts this date format -> 2022-07-21T14:38:36.408+01:00
    to this other format -> 2022-07-21 14:38:36.408
    """
    received_date = received_date.replace("T", " ")
    received_date = received_date.split("+")
    received_date = received_date[0]
    date_object = datetime.strptime(received_date, "%Y-%m-%d %H:%M:%S.%f")

    return date_object


def extract_number_of_sample(fastq_name):
    """
    This function extract number of sample from this type of data
    Example: from 214821_S12_R1_001.fastq.gz_214821_S12_R2_001.fastq.gz we extract 214821
    """
    data = fastq_name.split("_")
    data = data[0]
    return data
