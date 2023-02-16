from django.shortcuts import render

from relecov_documentation.utils.markdown_handling import (
    markdown_to_html,
    fix_img_folder,
)


def index(request):
    converted_to_html = markdown_to_html("index.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )


def description(request):
    converted_to_html = markdown_to_html("description.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )


def relecov_install(request):
    converted_to_html = markdown_to_html("relecov_install.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )


def configuration(request):
    converted_to_html = markdown_to_html("configuration.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )


def metadata(request):
    converted_to_html = markdown_to_html("metadata.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )


def metadata_lab_excel(request):
    converted_to_html = markdown_to_html("metadata_lab_excel.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )


def relecov_tools(request):
    converted_to_html = markdown_to_html("relecov_tools.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )


def intranet(request):
    converted_to_html = markdown_to_html("intranet.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )


def intranet(request):
    converted_to_html = markdown_to_html("intranet.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )


def upload_metadata_lab(request):
    converted_to_html = markdown_to_html("upload_metadata_lab.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )


def intranet_dashboard(request):
    converted_to_html = markdown_to_html("intranet_dashboard.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )


def upload_metadata_lab(request):
    converted_to_html = markdown_to_html("upload_metadata_lab.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )


def variant_dashboard(request):
    converted_to_html = markdown_to_html("variant_dashboard.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )


def methodology_dashboard(request):
    converted_to_html = markdown_to_html("methodology_dashboard.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )


def nextstrain_install(request):
    converted_to_html = markdown_to_html("nextstrain_install.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )


def howto_nextstrain(request):
    converted_to_html = markdown_to_html("howto_nextstrain.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )


def upload_to_ena(request):
    converted_to_html = markdown_to_html("upload_to_ena.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )


def upload_to_gisaid(request):
    converted_to_html = markdown_to_html("upload_to_gisaid.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )


def api_schema(request):
    converted_to_html = markdown_to_html("api_schema.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )


def howto_api(request):
    converted_to_html = markdown_to_html("howto_api.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )


def create_new_user(request):
    converted_to_html = markdown_to_html("createNewUserAccount.md")
    if isinstance(converted_to_html, dict):
        return render(request, "relecov_documentation/error_404.html")
    converted_to_html = fix_img_folder(converted_to_html)
    return render(
        request,
        "relecov_documentation/base.html",
        {"html": converted_to_html},
    )
