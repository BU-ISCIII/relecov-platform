from django.shortcuts import render  # , redirect

# from django.contrib.auth.decorators import login_required

from relecov_documentation.utils.markdown_handling import (
    generate_html_from_markdown_file2,
)


# Create your views here.
def documentation(request):
    html_visualization_from_markdown = generate_html_from_markdown_file2(
        "documentation.md"
    )

    return render(
        request,
        "relecov_documentation/documentation.html",
        {"html_visualization": html_visualization_from_markdown},
    )


def documentation_create_user_account(request):
    html_visualization_from_markdown = generate_html_from_markdown_file2(
        "create_user_account.md"
    )

    return render(
        request,
        "relecov_documentation/documentation.html",
        {"html_visualization": html_visualization_from_markdown},
    )


def documentation_access_to_intranet(request):
    html_visualization_from_markdown = generate_html_from_markdown_file2(
        "access_to_intranet.md"
    )

    return render(
        request,
        "relecov_documentation/documentation.html",
        {"html_visualization": html_visualization_from_markdown},
    )
