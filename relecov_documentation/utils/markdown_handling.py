import os

from django.conf import settings

from markdownx.utils import markdownify
import markdown

from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html


register = template.Library()

@register.filter
def do_something(title, content):

    something = '<h1>%s</h1><p>%s</p>' % (title, content)
    return mark_safe(something)


def testing():
    html = format_html("<h1>Hello</h1>")
    return html


def generate_html_from_markdown_file(markdown_file):
    html_dict = {}
    html_list = []
    html = ""
    try:
        markdown_doc = os.path.join(
            settings.BASE_DIR, "relecov_documentation", "markdown_files", markdown_file
        )
        with open(markdown_doc, "r") as fh:
            for line in fh:
                html_list.append(line)
                # html += markdownify(line)

    except FileNotFoundError:
        print("File doesn't exists")
        return "ERROR FILE NOT FOUND"
    for html_line in html_list[4:]:
        html += markdownify(html_line)

    html_dict["title"] = markdownify(html_list[0])
    html_dict["sub_title"] = markdownify(html_list[2])
    html_dict["body"] = html

    return html_dict


def fix_img_folder(text):
    """Change the image folder inside the markdown_files to the the static"""

    new_text = text.replace("img/", "../../static/relecov_documentation/img/")
    return new_text


def markdown_to_html(m_file):
    m_path = os.path.join(
        settings.BASE_DIR, "relecov_documentation", "markdown_files", m_file
    )
    if not os.path.isfile(m_path):
        return {"ERROR": "FILE NOT FOUND"}
    with open(m_path, "r") as fh:
        text = fh.read()
    return markdown.markdown(text, extensions=["toc", "tables"])

