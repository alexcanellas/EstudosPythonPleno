from django.urls import path
from . import views

app_name = 'banco_dados_avancado'

urlpatterns = [
    path('', views.index, name='index'),
]