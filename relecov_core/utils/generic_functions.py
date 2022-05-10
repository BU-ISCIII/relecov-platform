import time
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from relecov_core.core_config import METADATA_UPLOAD_FOLDER
# from django.conf import settings

import os

from relecov_platform.settings import MEDIA_URL


def store_file(user_file, folder):
    """
    Description:
        The function save the user input file
    Input:
        user_file # contains the file
        folder      subfolder to store the file
    Return:
        file_name
    """
    filename, file_extension = os.path.splitext(user_file.name)
    file_name = filename + "_" + str(time.strftime("%Y%m%d-%H%M%S")) + file_extension
    path_file = os.path.join(folder, file_name)
    path_to_metadata_folder =  os.path.join(settings.MEDIA_ROOT, "metadata")
    # saved_file = os.path.join(settings.MEDIA_ROOT, path_file)
    saved_file = os.path.join(path_to_metadata_folder, path_file)
    fs = FileSystemStorage()
    fs.save(saved_file, user_file)
    return path_file
