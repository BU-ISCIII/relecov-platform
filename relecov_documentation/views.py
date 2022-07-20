from django.shortcuts import render  # , redirect

# from django.contrib.auth.decorators import login_required

from relecov_documentation.utils.markdown_handling import (
    generate_html_from_markdown_file,
)

from django.http import Http404


# Create your views here.
def documentation(request):
    html_visualization_from_markdown = generate_html_from_markdown_file(
        "documentation.md"
    )

    return render(
        request,
        "relecov_documentation/documentation.html",
        {"html_visualization": html_visualization_from_markdown},
    )


def documentation_login(request):
    html_visualization_from_markdown = generate_html_from_markdown_file("login.md")
    # if html_visualization_from_markdown == "ERROR FILE NOT FOUND":
    #     raise Http404("File does not exist")

    
    return render(
        request,
        "relecov_documentation/documentation.html",
        {"html_visualization": html_visualization_from_markdown},
    )


def documentation_access_to_intranet(request):
    html_visualization_from_markdown = generate_html_from_markdown_file(
        "access_to_intranet.md"
    )

    return render(
        request,
        "relecov_documentation/documentation.html",
        {"html_visualization": html_visualization_from_markdown},
    )
