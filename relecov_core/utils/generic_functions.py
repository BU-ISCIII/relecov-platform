import time
from django.core.files.storage import FileSystemStorage
from django.conf import settings

# from django.conf import settings

import os


def store_file(user_file, folder):
    '''
    Description:
        The function save the user input file
    Input:
        user_file # contains the file
        folder      subfolder to store the file
    Return:
        file_name
    '''
    filename, file_extension = os.path.splitext(user_file.name)
    file_name = filename + '_' + str(time.strftime("%Y%m%d-%H%M%S")) + file_extension
    fs = FileSystemStorage()
    saved_file = os.path.join(settings.MEDIA_ROOT, folder, file_name)
    filename = fs.save(saved_file, user_file)
    return file_name
