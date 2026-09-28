from django.urls import path
from . import views

app_name = 'estruturas_dados'

urlpatterns = [
    path('', views.index, name='index'),
]