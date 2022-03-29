from django.http import HttpResponse
from django.shortcuts import render


# Create your views here.
def index(request):
    context = {}
    return render(request, 'relecov_core/index.html', context)

def dashboard(request):
    context = {}
    return render(request, 'relecov_core/methodology.html', context)
    
def variants(request):
    context = {}
    return render(request, 'relecov_core/variants.html', context)

def documentation(request):
    context = {}
    return render(request, 'relecov_core/documentation.html', context)