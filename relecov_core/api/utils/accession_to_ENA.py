import os
from django.conf import settings
import xml.etree.ElementTree as ET

# from django.utils.dateparse import parse_datetime


def parse_xml():
    """
    type(child.tag), type(child.attrib) -> <class 'str'> <class 'dict'>
    """
    xml_file_path = os.path.join(settings.BASE_DIR, "documents", "xml", "receipt.xml")
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    for child in root:
        # print(type(child.tag), type(child.attrib))
        print(child.tag, child.attrib)


def date_converter(received_date):
    """
    This function converts this date format -> 2022-07-21T14:38:36.408+01:00
    to this other format -> 2022-07-21 14:38:36.408
    """
    received_date = received_date.replace("T", " ")
    received_date = received_date.split("+")
    process_date = received_date[0]

    # parse_date = parse_datetime("2022-07-21T14:38:36.408+01:00")

    return process_date
