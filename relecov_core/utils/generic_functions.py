import time
from django.core.files.storage import FileSystemStorage
# from django.conf import settings
from relecov_core.core_config import SCHEMAS_UPLOAD_FOLDER
import os


def store_file(user_file):
    '''
    Description:
        The function save the user input file
    Input:
        request # contains the session information
    Return:
        Return True if the user belongs to Wetlab Manager, False if not
    '''

    filename, file_extension = os.path.splitext(user_file.name)
    file_name = filename + '_' + str(time.strftime("%Y%m%d-%H%M%S")) + file_extension
    fs = FileSystemStorage()
    import pdb; pdb.set_trace()
    filename = fs.save(file_name, user_file)
    saved_file = os.path.join(settings.MEDIA_ROOT, SCHEMAS_UPLOAD_FOLDER, file_name)
    return file_name
