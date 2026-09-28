"""
TEST_E2E.PY: testa o FLUXO COMPLETO, como um cliente da API faria.

Rodar só os e2e:
    pytest -m e2e -v

O teste só fala HTTP (APIClient). Não chama serializer nem ORM
diretamente. Isso exercita URL -> permission -> view -> serializer ->
banco -> resposta, tudo de uma vez.

Nota: "e2e de verdade" (navegador clicando na tela) usaria Playwright
ou Selenium. Este é o e2e no nível da API, o que mais se usa em backend.
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

pytestmark = pytest.mark.e2e


@pytest.fixture
def usuario(db):
    return get_user_model().objects.create_user(username="dev", password="senha-de-teste-123")


def test_fluxo_completo_de_um_autor(usuario):
    client = APIClient()
    url_lista = reverse("django_drf_avancado:autor-list")
    novo = {"nome": "Clarice Lispector", "nacionalidade": "Brasileira"}

    # 1) Anônimo tenta criar: a permission barra (403)
    resposta = client.post(url_lista, novo, format="json")
    assert resposta.status_code == 403

    # 2) Autentica e cria: 201 Created
    client.force_authenticate(user=usuario)
    resposta = client.post(url_lista, novo, format="json")
    assert resposta.status_code == 201
    autor_id = resposta.data["id"]

    # 3) O autor aparece na listagem
    resposta = client.get(url_lista)
    assert resposta.status_code == 200
    assert "Clarice Lispector" in [a["nome"] for a in resposta.data]

    # 4) Atualiza parcialmente (PATCH)
    url_detalhe = reverse("django_drf_avancado:autor-detail", args=[autor_id])
    resposta = client.patch(url_detalhe, {"nacionalidade": "Ucraniana-Brasileira"}, format="json")
    assert resposta.status_code == 200
    assert resposta.data["nacionalidade"] == "Ucraniana-Brasileira"

    # 5) Deleta: 204 No Content, e depois 404
    assert client.delete(url_detalhe).status_code == 204
    assert client.get(url_detalhe).status_code == 404


def test_leitura_e_publica(db):
    # sem autenticar, GET na listagem é permitido (200)
    resposta = APIClient().get(reverse("django_drf_avancado:autor-list"))
    assert resposta.status_code == 200


def test_patch_parcial_so_com_nome(usuario, autor_exemplo):
    # Regressão: PATCH mandando SÓ um campo não pode exigir os outros.
    client = APIClient()
    client.force_authenticate(user=usuario)
    url = reverse("django_drf_avancado:autor-detail", args=[autor_exemplo.id])

    resposta = client.patch(url, {"nome": "Machado de Assis Jr."}, format="json")

    assert resposta.status_code == 200, resposta.data  # o .data mostra o motivo se falhar
    assert resposta.data["nome"] == "Machado de Assis Jr."