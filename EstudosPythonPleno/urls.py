"""
URL configuration for EstudosPythonPleno project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Índice geral (página inicial com os links)
    path('', include('core.urls')),

    # Categoria 1: Python "de verdade"
    path('oop-avancado/', include('oop_avancado.urls')),
    path('estruturas-dados/', include('estruturas_dados.urls')),
    path('generators-iterators/', include('generators_iterators.urls')),
    path('decorators/', include('decorators.urls')),
    path('context-managers/', include('context_managers.urls')),
    path('concorrencia/', include('concorrencia.urls')),
    path('excecoes-typing/', include('excecoes_typing.urls')),
    path('django-drf-avancado/', include('django_drf_avancado.urls')),
    path('banco-dados-avancado/', include('banco_dados_avancado.urls')),
    path('testes-avancado/', include('testes_avancado.urls')),
     path('infra-ferramentas/', include('infra_ferramentas.urls')),
]
