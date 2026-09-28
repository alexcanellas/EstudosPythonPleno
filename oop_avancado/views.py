from django.shortcuts import render


def index(request):
    return render(request, 'oop_avancado/index.html')