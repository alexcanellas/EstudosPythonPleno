from django.urls import path
from . import views

app_name = 'infra_ferramentas'

urlpatterns = [
    path('', views.index, name='index'),
]