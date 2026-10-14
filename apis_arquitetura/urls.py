from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

app_name = 'apis_arquitetura'

urlpatterns = [
    path('', views.index, name='index'),

    # Status codes e idempotência
    path('api/livros/', views.LivroListaView.as_view(), name='livro-lista'),
    path('api/livros/<int:pk>/', views.LivroDetalheView.as_view(), name='livro-detalhe'),

    # Autenticação JWT
    # token/: troca usuário + senha por um par access + refresh
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token-obter'),
    # token/refresh/: troca um refresh válido por um access novo
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('api/auth/perfil/', views.PerfilView.as_view(), name='perfil'),
    path('api/auth/somente-admin/', views.SomenteAdminView.as_view(), name='somente-admin'),
    # Versionamento: o trecho <str:version> chega à view como "v1" ou "v2"
    path('api/<str:version>/livros/', views.LivroVersionadoView.as_view(), name='livro-versionado'),

    # Service layer
    path('camadas/livros/', views.LivroCamadasView.as_view(), name='livro-camadas'),
    path('camadas/livros/<int:pk>/desconto/', views.LivroDescontoView.as_view(), name='livro-desconto'),
]
