"""
TEST_PARAMETRIZE.PY — roda o MESMO teste várias vezes, com entradas
diferentes, sem duplicar código.

Rodar:
    pytest testes_avancado/test_parametrize.py -v
"""

import pytest
from decimal import Decimal
from django_drf_avancado.models import Autor, Livro


# ---------------------------------------------------------------------------
# 1. PARAMETRIZE BÁSICO — uma lista de tuplas (entrada, resultado_esperado)
# ---------------------------------------------------------------------------
# Sem parametrize, você escreveria um teste separado pra cada caso:
#   def test_soma_positivos(): assert soma(2, 3) == 5
#   def test_soma_negativos(): assert soma(-2, -3) == -5
#   def test_soma_zero(): assert soma(0, 0) == 0
# Com parametrize, é UM teste só, rodado 3 vezes — o pytest até numera
# cada execução separadamente no relatório (test_soma[2-3-5], etc).

def soma(a, b):
    return a + b


@pytest.mark.parametrize("a, b, esperado", [
    (2, 3, 5),
    (-2, -3, -5),
    (0, 0, 0),
    (100, -100, 0),
])
def test_soma(a, b, esperado):
    assert soma(a, b) == esperado


# ---------------------------------------------------------------------------
# 2. PARAMETRIZE COM IDS — nomes legíveis pra cada caso no relatório
# ---------------------------------------------------------------------------
# Por padrão, o pytest gera um nome meio críptico pra cada combinação
# (tipo test_validar_cep[12345-678-True]). Com `ids=`, você dá nomes
# legíveis — MUITO mais fácil de entender qual caso falhou, numa suíte
# grande.

def validar_cep(cep):
    """CEP brasileiro válido: 8 dígitos, com ou sem hífen."""
    cep_limpo = cep.replace("-", "")
    return cep_limpo.isdigit() and len(cep_limpo) == 8


@pytest.mark.parametrize("cep, esperado", [
    ("12345-678", True),
    ("12345678", True),
    ("123", False),
    ("abcde-fgh", False),
    ("", False),
], ids=[
    "cep_com_hifen_valido",
    "cep_sem_hifen_valido",
    "cep_muito_curto",
    "cep_com_letras",
    "cep_vazio",
])
def test_validar_cep(cep, esperado):
    assert validar_cep(cep) == esperado


# ---------------------------------------------------------------------------
# 3. PARAMETRIZE INTEGRADO COM BANCO — combinando com fixture
# ---------------------------------------------------------------------------
# parametrize e fixture não são excludentes — um teste pode usar os dois
# ao mesmo tempo. Aqui, cada combinação de parametrize roda com acesso
# ao banco de teste (via a fixture `db`, do pytest-django).

@pytest.mark.parametrize("preco, desconto_percentual, preco_esperado", [
    (Decimal("100.00"), 10, Decimal("90.00")),
    (Decimal("50.00"), 50, Decimal("25.00")),
    (Decimal("30.00"), 0, Decimal("30.00")),
])
def test_aplicar_desconto_em_livro(db, preco, desconto_percentual, preco_esperado):
    autor = Autor.objects.create(nome="Autor Teste", nacionalidade="Teste")
    livro = Livro.objects.create(
        titulo="Livro Teste",
        autor=autor,
        ano_publicacao=2024,
        preco=preco,
    )

    fator = Decimal(str(1 - desconto_percentual / 100))
    livro.preco = livro.preco * fator
    livro.save()

    assert livro.preco == preco_esperado


# ---------------------------------------------------------------------------
# 4. PARAMETRIZE ANINHADO — multiplicando dois conjuntos de parâmetros
# ---------------------------------------------------------------------------
# Empilhar dois @parametrize faz o pytest testar TODAS as combinações
# entre eles (produto cartesiano) — aqui, 3 nacionalidades x 2 nomes = 6
# testes gerados a partir de só 5 linhas de código.

@pytest.mark.parametrize("nacionalidade", ["Brasileira", "Britânica", "Francesa"])
@pytest.mark.parametrize("nome", ["Autor A", "Autor B"])
def test_criar_autor_com_combinacoes(db, nome, nacionalidade):
    autor = Autor.objects.create(nome=nome, nacionalidade=nacionalidade)
    assert autor.nome == nome
    assert autor.nacionalidade == nacionalidade