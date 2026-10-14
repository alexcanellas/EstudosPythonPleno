from django.urls import path
from . import views

app_name = 'boas_praticas'

urlpatterns = [
    path('', views.index, name='index'),
]