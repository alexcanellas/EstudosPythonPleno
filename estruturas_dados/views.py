from django.shortcuts import render


def index(request):
    return render(request, 'estruturas_dados/index.html')