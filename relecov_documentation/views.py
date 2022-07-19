from django.shortcuts import render, redirect

# from django.contrib.auth.decorators import login_required
from relecov_documentation.utils.markdown_handling import (
    generate_html_from_markdown_file,
)


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
