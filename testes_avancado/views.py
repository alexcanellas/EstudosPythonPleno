from django.shortcuts import render


def index(request):
    return render(request, 'testes_avancado/index.html')
