from django.shortcuts import render
from rest_framework import viewsets

from django_drf_avancado.models import Autor, Livro
from django_drf_avancado.serializers import AutorSerializer, LivroSerializer
from django_drf_avancado.permissions import ApenasLeituraOuAutenticado


def index(request):
    return render(request, 'django_drf_avancado/index.html')


class AutorViewSet(viewsets.ModelViewSet):
    serializer_class = AutorSerializer
    permission_classes = [ApenasLeituraOuAutenticado]

    def get_queryset(self):
        # prefetch_related aqui é o que evita N+1 quando o serializer
        # aninha `livros` dentro do JSON de cada autor — sem isso, listar
        # autores dispararia 1 query extra POR autor pra montar a lista
        # de livros de cada um
        return Autor.objects.prefetch_related('livros').all()


class LivroViewSet(viewsets.ModelViewSet):
    serializer_class = LivroSerializer
    permission_classes = [ApenasLeituraOuAutenticado]

    def get_queryset(self):
        # select_related aqui, mesmo o LivroSerializer não expondo o
        # autor diretamente — fica pronto pro dia que você quiser
        # adicionar esse campo ao serializer sem precisar lembrar de
        # otimizar depois
        return Livro.objects.select_related('autor').all()