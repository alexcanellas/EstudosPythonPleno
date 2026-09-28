from django.urls import path
from . import views

app_name = 'excecoes_typing'

urlpatterns = [
    path('', views.index, name='index'),
]