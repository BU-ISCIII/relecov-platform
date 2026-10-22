import os

from django.conf import settings
import markdown

# from django import template


def fix_img_folder(text):
    """Change the image folder inside the markdown_files to the the static"""
    new_text = text.replace("img/", "../../static/docs/img/")
    return new_text


def remove_md_extension(text):
    """Remove the .md extension in the link references"""
    return text.replace(".md", "")


def markdown_to_html(m_file):
    m_path = os.path.join(settings.BASE_DIR, "docs", "markdown_files", m_file)
    if not os.path.isfile(m_path):
        return {"ERROR": "FILE NOT FOUND"}
    with open(m_path, "r", encoding="utf-8") as fh:
        text = fh.read()
        text = remove_md_extension(text)
    html = markdown.markdown(text, extensions=["toc", "extra", "codehilite"])
    html = html.replace("<table>", '<table class="table table-bordered table-hover">')
    return html
