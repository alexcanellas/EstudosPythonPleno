"""
TEST_UNITARIO.PY: testa UMA peça isolada por vez, SEM tocar no banco.

Rodar só os unitários:
    pytest -m unitario -v

Repare que nenhum teste aqui pede a fixture `db`. O pytest-django BLOQUEIA
acesso ao banco em testes sem `db`: se algum deles tentasse consultar o
banco, quebraria com erro. Isso PROVA que estes testes são realmente
unitários (sem dependência de banco).
"""

import pytest
from types import SimpleNamespace

from django_drf_avancado.serializers import AutorSerializer
from django_drf_avancado.permissions import ApenasLeituraOuAutenticado

# aplica o marker "unitario" a TODOS os testes deste arquivo
pytestmark = pytest.mark.unitario


# ---------------------------------------------------------------------------
# 1. Validação do serializer, sem salvar nada
# ---------------------------------------------------------------------------
# is_valid() só roda as regras de validação em memória. Não grava no banco.

def test_serializer_aceita_dados_validos():
    serializer = AutorSerializer(data={"nome": "Machado", "nacionalidade": "Brasileira"})
    assert serializer.is_valid()


def test_serializer_rejeita_nome_curto():
    serializer = AutorSerializer(data={"nome": "A", "nacionalidade": "Brasileira"})

    assert not serializer.is_valid()
    assert "nome" in serializer.errors  # o erro vem indexado pelo campo


# ---------------------------------------------------------------------------
# 2. Método isolado, com a dependência substituída por um mock
# ---------------------------------------------------------------------------
# get_quantidade_livros(obj) chama obj.livros.count(), que iria ao banco.
# Aqui entregamos um objeto FALSO no lugar do Autor real, então o teste
# verifica só a lógica do método, sem banco.

def test_quantidade_livros_com_objeto_falso(mocker):
    autor_falso = mocker.Mock()
    autor_falso.livros.count.return_value = 3

    resultado = AutorSerializer().get_quantidade_livros(autor_falso)

    assert resultado == 3
    autor_falso.livros.count.assert_called_once()


# ---------------------------------------------------------------------------
# 3. Permission testada com um request falso
# ---------------------------------------------------------------------------
# has_permission só olha request.method e request.user.is_authenticated.
# SimpleNamespace cria um objeto com os atributos que precisamos, sem
# montar um request HTTP de verdade.

@pytest.mark.parametrize("metodo, autenticado, esperado", [
    ("GET", False, True),     # leitura: qualquer um pode
    ("POST", False, False),   # escrita anônima: bloqueia
    ("POST", True, True),     # escrita autenticada: libera
    ("DELETE", False, False), # deleção anônima: bloqueia
], ids=["leitura_anonima", "escrita_anonima", "escrita_autenticada", "delete_anonimo"])
def test_permission_apenas_leitura_ou_autenticado(metodo, autenticado, esperado):
    request = SimpleNamespace(
        method=metodo,
        user=SimpleNamespace(is_authenticated=autenticado),
    )

    permissao = ApenasLeituraOuAutenticado()

    assert permissao.has_permission(request, view=None) == esperado