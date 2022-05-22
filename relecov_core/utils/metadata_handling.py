import datetime
import os
from pathlib import Path

from relecov_core.core_config import METADATA_UPLOAD_FOLDER

# from relecov_core.utils.generic_functions import store_file
from relecov_core.models import Document


def upload_excel_file(request):
    sample_recorded = {}
    file_path = datetime.date.today().strftime("%Y_%m_%d")
    date = datetime.date.today().strftime("%Y-%m-%d_%H:%M:%S")
    user_name = request.user.username
    title = "metadata_{}_{}".format(user_name, date)
    file_path = datetime.date.today().strftime("%Y_%m_%d")

    # Fetching the form data
    uploadedFile = request.FILES["samplesExcel"]
    # Create a folder per day if it doesn't exist
    path = os.path.join(METADATA_UPLOAD_FOLDER, file_path)
    if not os.path.exists(path):
        path = Path(path)
        path.mkdir(parents=True)

    # Saving the information in the database
    document = Document(title=title, file_path=path, uploadedFile=uploadedFile)
    document.save()
    sample_recorded["process"] = "File Upload"

    return sample_recorded
