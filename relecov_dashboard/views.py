from django.shortcuts import render

def dashboard(request):
    context = {}
    return render(request, 'relecov_core/methodology.html', context)