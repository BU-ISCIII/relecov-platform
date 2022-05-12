import datetime
import os
from pathlib import Path

# import xlrd
from relecov_core.core_config import METADATA_UPLOAD_FOLDER
from relecov_core.utils.generic_functions import store_file
from relecov_core.models import Document


def upload_excel_file(request):
    sample_recorded = {}
    file_path = datetime.date.today().strftime("%Y_%m_%d")
    date = datetime.date.today().strftime("%Y-%m-%d_%H:%M:%S")
    user_name = request.user.username
    title = "metadata_{}_{}".format(user_name, date)
    file_path = datetime.date.today().strftime("%Y_%m_%d")
    print(title)

    # Fetching the form data
    uploadedFile = request.FILES["samplesExcel"]
    # Create a folder per day if it doesn't exist
    path = os.path.join(METADATA_UPLOAD_FOLDER, file_path)
    if not os.path.exists(path):
        path = Path(path)
        path.mkdir(parents=True)
    # Saving the information in the database
    # file_upload = store_file(uploadedFile, file_path)
    # print(file_upload)
    document = Document(title=title, file_path=path, uploadedFile=uploadedFile)
    document.save()

    """
    # read excel file xlrd example
    book = xlrd.open_workbook(
        "documents/metadata/2022_05_08/METADATA_LAB_RESPIRATORIOS_V2.xlsx"
    )
    print("The number of worksheets is {0}".format(book.nsheets))
    print("Worksheet name(s): {0}".format(book.sheet_names()))
    sh = book.sheet_by_index(1)
    print("{0} {1} {2}".format(sh.name, sh.nrows, sh.ncols))
    print("Cell D30 is {0}".format(sh.cell_value(rowx=29, colx=3)))
    # for rx in range(sh.nrows):
    #    print(type(sh.row(rx)))
    print(type(sh.row(0)))
    print(sh.row(0))
    sample_recorded["Process"] = "fichero_recibido"
    """
    return sample_recorded
