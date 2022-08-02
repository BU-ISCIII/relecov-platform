from django.shortcuts import render  # , redirect

# from django.contrib.auth.decorators import login_required

from relecov_documentation.utils.markdown_handling import (
    generate_html_from_markdown_file,
    markdown_to_html,
    fix_img_folder,
)


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
    html_visualization_from_markdown = generate_html_from_markdown_file(
        "create_user_account.md"
    )

    return render(
        request,
        "relecov_documentation/documentation.html",
        {"html_visualization": html_visualization_from_markdown},
    )


def intranet(request):
    html_visualization_from_markdown = generate_html_from_markdown_file("intranet.md")

    return render(
        request,
        "relecov_documentation/documentation.html",
        {"html_visualization": html_visualization_from_markdown},
    )


def dashboard(request):
    html_visualization_from_markdown = generate_html_from_markdown_file("dashboard.md")

    return render(
        request,
        "relecov_documentation/documentation.html",
        {"html_visualization": html_visualization_from_markdown},
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
