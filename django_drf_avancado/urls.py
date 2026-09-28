from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'django_drf_avancado'

router = DefaultRouter()
router.register('autores', views.AutorViewSet, basename='autor')
router.register('livros', views.LivroViewSet, basename='livro')

urlpatterns = [
    path('', views.index, name='index'),
    path('api/', include(router.urls)),
]