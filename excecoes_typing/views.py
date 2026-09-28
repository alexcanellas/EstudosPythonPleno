from django.shortcuts import render


def index(request):
    return render(request, 'excecoes_typing/index.html')