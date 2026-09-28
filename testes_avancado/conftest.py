"""
CONFTEST.PY — fixtures compartilhadas para todos os testes desse app.

O pytest descobre esse arquivo sozinho (pelo nome exato "conftest.py") e
injeta qualquer fixture daqui em qualquer teste que declarar um parâmetro
com o mesmo nome — sem precisar de import nenhum nos arquivos de teste.
"""

import pytest
from django_drf_avancado.models import Autor, Livro


# ---------------------------------------------------------------------------
# 1. FIXTURE BÁSICA — prepara um dado e devolve
# ---------------------------------------------------------------------------
# @pytest.fixture marca a função como fixture. Qualquer teste que declarar
# um parâmetro chamado "autor_exemplo" recebe o RETORNO dessa função
# automaticamente, já pronto, antes do teste rodar.
#
# `db` aqui é uma fixture PRONTA do pytest-django — ela garante que existe
# um banco de teste disponível (criado e destruído automaticamente a cada
# rodada de testes, isolado do banco de desenvolvimento de verdade).

@pytest.fixture
def autor_exemplo(db):
    return Autor.objects.create(nome="Machado de Assis", nacionalidade="Brasileira")


@pytest.fixture
def livro_exemplo(autor_exemplo):
    # fixtures podem DEPENDER de outras fixtures — o pytest resolve a
    # cadeia sozinho (autor_exemplo é criado primeiro, depois esse aqui)
    return Livro.objects.create(
        titulo="Dom Casmurro",
        autor=autor_exemplo,
        ano_publicacao=1899,
        preco=29.90,
    )


# ---------------------------------------------------------------------------
# 2. FIXTURE COM yield — setup ANTES, teardown DEPOIS do teste
# ---------------------------------------------------------------------------
# Quando a fixture precisa fazer alguma LIMPEZA depois que o teste termina
# (fechar arquivo, deletar registro extra, desfazer alguma configuração),
# usa `yield` em vez de `return`. Tudo ANTES do yield é o setup, tudo
# DEPOIS é o teardown — roda mesmo se o teste falhar no meio.

@pytest.fixture
def autor_temporario_com_log(db):
    print("\n  [fixture] SETUP: criando autor temporário")
    autor = Autor.objects.create(nome="Autor Temporário de Teste", nacionalidade="Teste")

    yield autor  # o teste roda AQUI, recebendo o `autor` como valor da fixture

    print("  [fixture] TEARDOWN: removendo autor temporário")
    autor.delete()


# ---------------------------------------------------------------------------
# 3. ESCOPOS DE FIXTURE — quantas vezes ela roda
# ---------------------------------------------------------------------------
# Por padrão, uma fixture roda TODA VEZ que um teste pede ela (escopo
# "function", o padrão). Mas dá pra mudar isso com `scope=`:
#
#   scope="function"  -> roda 1x POR TESTE (padrão)
#   scope="class"     -> roda 1x POR CLASSE de teste
#   scope="module"     -> roda 1x POR ARQUIVO de teste
#   scope="session"    -> roda 1x PRA TODA a execução do pytest inteira
#
# Escopos maiores (session, module) são úteis pra coisas CARAS de montar
# (ex: subir um mock de serviço externo) que não precisam ser recriadas
# a cada teste individual — economiza tempo de execução da suíte inteira.

@pytest.fixture(scope="session")
def configuracao_cara_de_montar():
    print("\n  [fixture session] Montando configuração cara — isso deve "
          "aparecer só 1 VEZ, não importa quantos testes usem essa fixture")
    return {"api_key_simulada": "chave-de-teste-123"}