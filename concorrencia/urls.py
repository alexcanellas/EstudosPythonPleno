from django.urls import path
from . import views

app_name = 'concorrencia'

urlpatterns = [
    path('', views.index, name='index'),
]