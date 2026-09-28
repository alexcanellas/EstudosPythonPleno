from django.urls import path
from . import views

app_name = 'context_managers'

urlpatterns = [
    path('', views.index, name='index'),
]