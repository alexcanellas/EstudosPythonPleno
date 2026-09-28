"""
TEST_INTEGRACAO.PY: testa VÁRIAS peças trabalhando juntas (com banco).

Rodar só os de integração:
    pytest -m integracao -v

Aqui nada é mockado: serializer, ORM, viewset e signal rodam de verdade,
e o que se verifica é se as peças se encaixam.
"""

import pytest

from django_drf_avancado.models import Autor, Livro
from django_drf_avancado.serializers import AutorSerializer
from django_drf_avancado.views import AutorViewSet

pytestmark = pytest.mark.integracao


# ---------------------------------------------------------------------------
# 1. Serializer + ORM: o JSON aninhado sai certo a partir do banco?
# ---------------------------------------------------------------------------
def test_serializer_monta_autor_com_livros_aninhados(livro_exemplo):
    dados = AutorSerializer(livro_exemplo.autor).data

    assert dados["nome"] == "Machado de Assis"
    assert dados["quantidade_livros"] == 1
    assert dados["livros"][0]["titulo"] == "Dom Casmurro"


# ---------------------------------------------------------------------------
# 2. ViewSet + serializer + ORM: o prefetch_related evita o N+1?
# ---------------------------------------------------------------------------
# django_assert_num_queries é uma fixture do pytest-django: falha se o
# número de queries dentro do bloco for diferente do esperado.
# Este teste PROVA a otimização da Categoria 2: com prefetch_related,
# serializar N autores custa 2 queries (autores + todos os livros), e
# não 1 + N.

def test_viewset_nao_gera_n_mais_1(db, django_assert_num_queries):
    for i in range(3):
        autor = Autor.objects.create(nome=f"Autor {i}", nacionalidade="Teste")
        for j in range(2):
            Livro.objects.create(
                titulo=f"Livro {i}-{j}", autor=autor, ano_publicacao=2000, preco=10
            )

    queryset = AutorViewSet().get_queryset()

    with django_assert_num_queries(2):
        dados = AutorSerializer(queryset, many=True).data
        assert len(dados) == 3


# ---------------------------------------------------------------------------
# 3. Model + signal: criar um Livro dispara o post_save?
# ---------------------------------------------------------------------------
# capsys captura o que foi impresso (print). Como o signal imprime,
# dá pra verificar que ele disparou.

def test_signal_dispara_ao_criar_livro(autor_exemplo, capsys):
    Livro.objects.create(
        titulo="Quincas Borba", autor=autor_exemplo, ano_publicacao=1891, preco=27.5
    )

    saida = capsys.readouterr().out
    assert "[signal] Novo livro criado" in saida
    assert "Quincas Borba" in saida