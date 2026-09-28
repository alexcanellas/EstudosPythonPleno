from django.urls import path
from . import views

app_name = 'generators_iterators'

urlpatterns = [
    path('', views.index, name='index'),
]