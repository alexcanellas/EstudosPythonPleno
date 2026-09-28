from django.urls import path
from . import views

app_name = 'oop_avancado'

urlpatterns = [
    path('', views.index, name='index'),
]