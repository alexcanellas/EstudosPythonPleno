"""
TASKS.PY — tarefas assíncronas executadas pelo worker do Celery.

@shared_task marca uma função comum como uma "task": em vez de rodar na
hora, chamar task.delay(...) só ENFILEIRA ela no Redis, e devolve
imediatamente. Quem executa de verdade é um processo separado, o worker,
rodando em paralelo.
"""

import time
from celery import shared_task


@shared_task
def tarefa_demorada(segundos):
    """Simula um trabalho pesado (ex: gerar relatório, processar imagem)."""
    print(f"  [worker] Iniciando tarefa de {segundos}s...")
    time.sleep(segundos)
    print(f"  [worker] Tarefa de {segundos}s concluída!")
    return f"Processado após {segundos}s"


@shared_task
def enviar_email_simulado(destinatario, assunto):
    """Simula o envio de e-mail (o cenário clássico de 'não travar a
    requisição' — e-mail de verdade pode levar segundos pra responder)."""
    time.sleep(2)
    print(f"  [worker] E-mail '{assunto}' enviado para {destinatario}")
    return {"status": "enviado", "destinatario": destinatario}


@shared_task
def somar_async(a, b):
    """Task simples, só para provar passagem de argumentos e retorno."""
    resultado = a + b
    print(f"  [worker] {a} + {b} = {resultado}")
    return resultado


@shared_task
def tarefa_com_falha():
    """Dispara uma exceção de propósito — serve pra ver como o Celery
    reporta falha de uma task (diferente de uma task que teve sucesso)."""
    raise ValueError("Falha proposital para demonstração")