
from django.urls import path
from . import views

app_name = 'decorators'

urlpatterns = [
    path('', views.index, name='index'),
]