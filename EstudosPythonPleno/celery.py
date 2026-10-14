"""
EstudosPythonPleno/celery.py

Ponto de entrada do Celery para este projeto. Qualquer task registrada
em qualquer app (via tasks.py) é descoberta automaticamente a partir
daqui, sem precisar listar manualmente.
"""

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EstudosPythonPleno.settings')

app = Celery('EstudosPythonPleno')

# Lê toda configuração que comece com CELERY_ do settings.py
# (ex: CELERY_BROKER_URL vira broker_url)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Procura um tasks.py dentro de cada app listado em INSTALLED_APPS,
# e registra toda função marcada com @shared_task automaticamente.
app.autodiscover_tasks()