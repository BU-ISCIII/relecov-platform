from django.http import HttpResponse
from django.shortcuts import render


# Create your views here.
def index(request):
    context = {}
    return render(request, 'relecov_core/index.html', context)

def dashboard(request):
    context = {}
    return render(request, 'relecov_core/dashboard.html', context)
    
    