"""
TEST_MOCKS.PY: mocks com pytest-mock (mocker), monkeypatch e unittest.mock.

Rodar:
    pytest testes_avancado/test_mocks.py -v
"""

import pytest
from unittest import mock

from testes_avancado import servicos
from testes_avancado.servicos import processar_pedido, PagamentoRecusadoError


# ---------------------------------------------------------------------------
# 0. SEM MOCK: prova de que a função externa real explode
# ---------------------------------------------------------------------------
def test_sem_mock_chama_a_funcao_real():
    with pytest.raises(RuntimeError, match="gateway REAL"):
        processar_pedido(100, "4111", "a@b.com")


# ---------------------------------------------------------------------------
# 1. MOCK BÁSICO: mocker.patch + return_value
# ---------------------------------------------------------------------------
# REGRA DE OURO: patch-se o nome ONDE ELE É USADO, não onde foi definido.
# processar_pedido busca chamar_gateway_pagamento dentro do módulo
# "testes_avancado.servicos", então é esse caminho que entra no patch.
# (Se outro módulo fizesse `from servicos import chamar_gateway_pagamento`,
# o alvo seria o módulo DELE, porque o import copia a referência.)

def test_pedido_aprovado(mocker):
    gateway = mocker.patch(
        "testes_avancado.servicos.chamar_gateway_pagamento",
        return_value={"status": "aprovado", "id": "TX-123"},
    )
    email = mocker.patch("testes_avancado.servicos.enviar_email_confirmacao")

    resultado = processar_pedido(100, "4111", "cliente@email.com")

    assert resultado == {"status": "ok", "transacao": "TX-123"}


# ---------------------------------------------------------------------------
# 2. VERIFICANDO COMO O MOCK FOI CHAMADO
# ---------------------------------------------------------------------------
# Mock guarda o histórico das chamadas. Dá pra testar não só o RESULTADO,
# mas o COMPORTAMENTO: "chamou o gateway com os argumentos certos?"

def test_gateway_recebe_argumentos_corretos(mocker):
    gateway = mocker.patch(
        "testes_avancado.servicos.chamar_gateway_pagamento",
        return_value={"status": "aprovado", "id": "TX-1"},
    )
    email = mocker.patch("testes_avancado.servicos.enviar_email_confirmacao")

    processar_pedido(250, "4111", "cliente@email.com")

    gateway.assert_called_once_with(250, "4111")
    email.assert_called_once_with("cliente@email.com", "Pagamento de 250 aprovado")
    assert gateway.call_count == 1


# ---------------------------------------------------------------------------
# 3. side_effect: SIMULANDO FALHA (exceção)
# ---------------------------------------------------------------------------
# return_value devolve um valor. side_effect pode LEVANTAR uma exceção,
# ideal pra testar os caminhos de erro, difíceis de reproduzir de verdade
# (gateway fora do ar, timeout, etc).

def test_gateway_fora_do_ar(mocker):
    mocker.patch(
        "testes_avancado.servicos.chamar_gateway_pagamento",
        side_effect=ConnectionError("timeout"),
    )
    email = mocker.patch("testes_avancado.servicos.enviar_email_confirmacao")

    resultado = processar_pedido(100, "4111", "cliente@email.com")

    assert resultado == {"status": "erro", "motivo": "gateway indisponível"}
    email.assert_not_called()  # se o pagamento falhou, NÃO pode mandar e-mail


# ---------------------------------------------------------------------------
# 4. TESTANDO QUE ALGO *NÃO* ACONTECEU
# ---------------------------------------------------------------------------
def test_pagamento_recusado_nao_envia_email(mocker):
    mocker.patch(
        "testes_avancado.servicos.chamar_gateway_pagamento",
        return_value={"status": "recusado", "id": "TX-2"},
    )
    email = mocker.patch("testes_avancado.servicos.enviar_email_confirmacao")

    with pytest.raises(PagamentoRecusadoError, match="recusado"):
        processar_pedido(100, "4111", "cliente@email.com")

    email.assert_not_called()


# ---------------------------------------------------------------------------
# 5. MONKEYPATCH: alterar variável de ambiente / atributo, com reversão
# ---------------------------------------------------------------------------
# monkeypatch é uma fixture nativa do pytest. Tudo que ela altera é
# DESFEITO automaticamente no fim do teste.

def test_monkeypatch_variavel_de_ambiente(monkeypatch):
    monkeypatch.setenv("AMBIENTE", "producao")
    assert servicos.modo_ambiente() == "producao"


def test_ambiente_voltou_ao_padrao():
    # roda DEPOIS do teste acima e prova a reversão automática
    assert servicos.modo_ambiente() == "desenvolvimento"


# ---------------------------------------------------------------------------
# 6. unittest.mock PURO: a mesma ideia, sem o plugin pytest-mock
# ---------------------------------------------------------------------------
# mocker é um "atalho" pro unittest.mock, com limpeza automática. Dá pra
# usar o original direto, com `with mock.patch(...)`. Você vai ver muito
# esse estilo em código legado.

def test_com_unittest_mock_puro():
    with mock.patch(
        "testes_avancado.servicos.chamar_gateway_pagamento",
        return_value={"status": "aprovado", "id": "TX-9"},
    ), mock.patch("testes_avancado.servicos.enviar_email_confirmacao"):
        resultado = processar_pedido(10, "4111", "x@y.com")

    assert resultado["transacao"] == "TX-9"