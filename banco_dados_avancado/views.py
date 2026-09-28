from django.shortcuts import render


def index(request):
    return render(request, 'banco_dados_avancado/index.html')