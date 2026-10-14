"""
TEST_SERVICE_LAYER.PY: testa as regras do LivroService com repositórios
FALSOS, em memória.

Rodar:
    pytest testes_avancado/test_service_layer.py -v

Nenhum teste aqui usa a fixture `db` nem o APIClient. O pytest-django
BLOQUEIA acesso ao banco em teste sem `db`: se o service tocasse no ORM,
estes testes quebrariam. Passarem prova que a regra de negócio está
isolada de verdade.
"""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from apis_arquitetura.services import (
    AnoPublicacaoInvalido,
    AutorNaoEncontrado,
    DescontoInvalido,
    LivroDuplicado,
    LivroNaoEncontrado,
    LivroService,
)

pytestmark = pytest.mark.unitario


# ---------------------------------------------------------------------------
# REPOSITÓRIOS FALSOS: mesma "forma" dos reais, mas guardam tudo num dict
# ---------------------------------------------------------------------------
class LivroRepositoryFalso:
    def __init__(self):
        self.itens = {}
        self._proximo_id = 1

    def obter(self, pk):
        return self.itens.get(pk)

    def existe_titulo_do_autor(self, titulo, autor_id):
        return any(
            livro.titulo.lower() == titulo.lower() and livro.autor_id == autor_id
            for livro in self.itens.values()
        )

    def criar(self, **dados):
        livro = SimpleNamespace(id=self._proximo_id, **dados)
        self.itens[livro.id] = livro
        self._proximo_id += 1
        return livro

    def atualizar_preco(self, livro, novo_preco):
        livro.preco = novo_preco
        return livro


class AutorRepositoryFalso:
    def __init__(self, ids):
        self.ids = set(ids)

    def existe(self, autor_id):
        return autor_id in self.ids


@pytest.fixture
def livros():
    return LivroRepositoryFalso()


@pytest.fixture
def service(livros):
    return LivroService(livros=livros, autores=AutorRepositoryFalso(ids=[1, 2]))


def _dados(**mudancas):
    base = dict(titulo='Dom Casmurro', autor_id=1, ano_publicacao=1899, preco=Decimal('29.90'))
    return {**base, **mudancas}


# ---------------------------------------------------------------------------
# criar
# ---------------------------------------------------------------------------
def test_criar_livro_valido(service, livros):
    livro = service.criar(**_dados())

    assert livro.id == 1
    assert livros.obter(livro.id) is livro


def test_ano_de_publicacao_no_futuro(service, livros):
    with pytest.raises(AnoPublicacaoInvalido):
        service.criar(**_dados(ano_publicacao=date.today().year + 1))

    assert livros.itens == {}  # a regra barrou ANTES de gravar


def test_autor_inexistente(service, livros):
    with pytest.raises(AutorNaoEncontrado):
        service.criar(**_dados(autor_id=999))

    assert livros.itens == {}


def test_titulo_duplicado_do_mesmo_autor(service):
    service.criar(**_dados(titulo='Quincas Borba'))

    with pytest.raises(LivroDuplicado):
        service.criar(**_dados(titulo='quincas borba'))  # só muda a caixa


def test_mesmo_titulo_de_autores_diferentes_e_permitido(service):
    service.criar(**_dados(titulo='Antologia', autor_id=1))
    outro = service.criar(**_dados(titulo='Antologia', autor_id=2))

    assert outro.autor_id == 2


# ---------------------------------------------------------------------------
# aplicar_desconto
# ---------------------------------------------------------------------------
@pytest.mark.parametrize('preco, percentual, esperado', [
    (Decimal('100.00'), 10, Decimal('90.00')),
    (Decimal('29.90'), 50, Decimal('14.95')),
    (Decimal('19.99'), 15, Decimal('16.99')),
], ids=['desconto_10pct', 'limite_de_50pct', 'arredondamento_2_casas'])
def test_aplicar_desconto(service, preco, percentual, esperado):
    livro = service.criar(**_dados(preco=preco))

    atualizado = service.aplicar_desconto(livro.id, percentual)

    assert atualizado.preco == esperado


@pytest.mark.parametrize('percentual', [0, -5, 51, 100],
                         ids=['zero', 'negativo', 'acima_do_limite', 'cem_por_cento'])
def test_desconto_fora_da_faixa(service, percentual):
    livro = service.criar(**_dados(preco=Decimal('100.00')))

    with pytest.raises(DescontoInvalido):
        service.aplicar_desconto(livro.id, percentual)

    assert livro.preco == Decimal('100.00')  # o preço não mudou


def test_desconto_em_livro_inexistente(service):
    with pytest.raises(LivroNaoEncontrado):
        service.aplicar_desconto(999, 10)