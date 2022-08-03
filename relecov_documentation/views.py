from django.shortcuts import render

from relecov_documentation.utils.markdown_handling import (
    do_something,
    generate_html_from_markdown_file,
    markdown_to_html,
    fix_img_folder,
)
from django.utils.html import format_html


# Create your views here.
def index(request):
    html_visualization_from_markdown = generate_html_from_markdown_file(
        "documentation.md"
    )

    return render(
        request,
        "relecov_documentation/documentation.html",
        {"html_visualization": html_visualization_from_markdown},
    )


def initial_configuration(request):
    converted_to_html = markdown_to_html("initial_configuration.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/documentation2.html",
        {"html": converted_to_html},
    )


def create_user_account(request):
    converted_to_html = markdown_to_html("create_user_account.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/documentation2.html",
        {"html": converted_to_html},
    )


def installation(request):
    converted_to_html = markdown_to_html("installation.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/documentation2.html",
        {"html": converted_to_html},
    )


def intranet(request):
    # html_visualization_from_markdown = generate_html_from_markdown_file("intranet.md")
    converted_to_html = markdown_to_html("intranet.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/documentation2.html",
        {"html": converted_to_html},
    )


def dashboard(request):
    converted_to_html = markdown_to_html("dashboard.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/documentation2.html",
        {"html": converted_to_html},
    )


def test(request):
    html = do_something(title="title", content="content")
    return render(
        request,
        "relecov_documentation/test.html",
        {"html": html},
    )


def test2(request):
    html = format_html("<h1>Hello</h1>")
    return render(
        request,
        "relecov_documentation/test2.html",
        {"html2": html},
    )


def results_download(request):
    converted_to_html = markdown_to_html("results_download.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/documentation2.html",
        {"html": converted_to_html},
    )


def results_info_processed(request):
    converted_to_html = markdown_to_html("results_info_processed.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/documentation2.html",
        {"html": converted_to_html},
    )
    

def results_info_received(request):
    converted_to_html = markdown_to_html("results_info_received.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/documentation2.html",
        {"html": converted_to_html},
    )



def upload_metadata_lab(request):
    converted_to_html = markdown_to_html("upload_metadata_lab.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/documentation2.html",
        {"html": converted_to_html},
    )

def upload_to_ena(request):
    converted_to_html = markdown_to_html("upload_to_ena.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/documentation2.html",
        {"html": converted_to_html},
    )
    

def upload_to_gisaid(request):
    converted_to_html = markdown_to_html("upload_to_gisaid.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/documentation2.html",
        {"html": converted_to_html},
    )