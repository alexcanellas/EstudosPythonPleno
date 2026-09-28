"""
SERVICOS.PY: código de "produção" que os testes de mock vão exercitar.

As funções chamar_gateway_pagamento e enviar_email_confirmacao simulam
serviços EXTERNOS (lentos, com custo real, ou com efeito colateral).
Elas levantam RuntimeError de propósito: se algum teste chamar uma delas
de verdade, ele quebra na hora. Isso prova que o mock realmente entrou
no lugar.
"""

import os
import time


class PagamentoRecusadoError(Exception):
    pass


def chamar_gateway_pagamento(valor, cartao):
    time.sleep(1)  # simula a lentidão de uma chamada de rede
    raise RuntimeError("Chamou o gateway REAL! Em teste isso não deveria acontecer.")


def enviar_email_confirmacao(email, mensagem):
    raise RuntimeError("Enviou e-mail REAL! Em teste isso não deveria acontecer.")


def modo_ambiente():
    # lê uma variável de ambiente, usada na demo do monkeypatch
    return os.environ.get("AMBIENTE", "desenvolvimento")


def processar_pedido(valor, cartao, email):
    """A LÓGICA DE NEGÓCIO que queremos testar (as chamadas externas ficam mockadas)."""
    try:
        resposta = chamar_gateway_pagamento(valor, cartao)
    except ConnectionError:
        return {"status": "erro", "motivo": "gateway indisponível"}

    if resposta["status"] != "aprovado":
        raise PagamentoRecusadoError(f"Pagamento recusado: {resposta['status']}")

    enviar_email_confirmacao(email, f"Pagamento de {valor} aprovado")
    return {"status": "ok", "transacao": resposta["id"]}