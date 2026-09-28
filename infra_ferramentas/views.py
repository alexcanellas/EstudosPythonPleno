from django.shortcuts import render

# Create your views here.

def index(request):
    return render(request, 'infra_ferramentas/index.html')