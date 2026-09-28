from django.shortcuts import render


def index(request):
    return render(request, 'generators_iterators/index.html')