import os

from django.conf import settings
from django.shortcuts import render

from markdownx.utils import markdownify


def generate_html_from_markdown_file(markdown_file):
    html = ""
    try:
        markdown_doc = os.path.join(
            settings.BASE_DIR, "relecov_documentation", "markdown_files", markdown_file
        )
        with open(markdown_doc, "r") as fh:
            for line in fh:
                html += markdownify(line)
    except FileNotFoundError:
        print("File doesn't exists")
        return "ERROR FILE NOT FOUND"
        
    return html
