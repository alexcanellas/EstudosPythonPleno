"""
TEST_FIXTURES.PY — prova o comportamento das fixtures do conftest.py.

Rodar só esse arquivo:
    pytest testes_avancado/test_fixtures.py -v -s

O -v (verbose) mostra o nome de cada teste. O -s desabilita a captura de
output do pytest, pra você VER os prints das fixtures (setup/teardown) —
sem o -s, o pytest esconde os prints de testes que passaram.
"""


# ---------------------------------------------------------------------------
# 1. Usando fixture básica — só declarando o parâmetro
# ---------------------------------------------------------------------------
# Repare: o teste não instancia nada, não importa nada do conftest.py.
# Só declarar um parâmetro chamado "autor_exemplo" já é suficiente pro
# pytest procurar uma fixture com esse nome e injetar o resultado dela.

def test_autor_foi_criado_corretamente(autor_exemplo):
    assert autor_exemplo.nome == "Machado de Assis"
    assert autor_exemplo.nacionalidade == "Brasileira"


def test_livro_depende_de_autor_exemplo(livro_exemplo):
    # livro_exemplo, por trás dos panos, já disparou autor_exemplo
    # primeiro (porque livro_exemplo DEPENDE dela no conftest.py)
    assert livro_exemplo.titulo == "Dom Casmurro"
    assert livro_exemplo.autor.nome == "Machado de Assis"


# ---------------------------------------------------------------------------
# 2. Fixture com yield — vendo o setup/teardown na prática
# ---------------------------------------------------------------------------
# Rode com -s pra ver os prints "[fixture] SETUP" e "[fixture] TEARDOWN"
# ao redor do print do próprio teste.

def test_autor_temporario_existe_durante_o_teste(autor_temporario_com_log):
    print("  [teste] rodando o teste em si, autor já existe")
    assert autor_temporario_com_log.nome == "Autor Temporário de Teste"
    # quando esse teste termina (com sucesso ou falha), o teardown do
    # yield roda automaticamente, deletando o autor


# ---------------------------------------------------------------------------
# 3. Escopo session — roda só 1 vez, mesmo em vários testes
# ---------------------------------------------------------------------------
# Os dois testes abaixo usam a MESMA fixture de escopo "session". Rodando
# com -s, o print "[fixture session] Montando configuração cara" deve
# aparecer UMA ÚNICA VEZ no terminal inteiro, não duas.

def test_usa_configuracao_cara_primeira_vez(configuracao_cara_de_montar):
    assert configuracao_cara_de_montar["api_key_simulada"] == "chave-de-teste-123"


def test_usa_configuracao_cara_segunda_vez(configuracao_cara_de_montar):
    # mesmo objeto Python, não uma cópia recriada
    assert configuracao_cara_de_montar["api_key_simulada"] == "chave-de-teste-123"