from django.shortcuts import render


def index(request):
    return render(request, 'context_managers/index.html')