from django.apps import AppConfig


class DjangoDrfAvancadoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_drf_avancado'

    def ready(self):
        # importa os signals aqui, não lá em cima do arquivo — isso evita
        # problemas de import circular durante a inicialização do Django
        import django_drf_avancado.signals
