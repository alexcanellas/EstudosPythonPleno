"""
CONTEXT MANAGERS — exemplos comentados.

Foco: o protocolo __enter__/__exit__, a versão com @contextmanager
(usando yield), e por que o __exit__ roda mesmo quando dá exceção.
Rode no shell:

    from context_managers.exemplos import *
    demo_context_manager_classe()
    demo_context_manager_com_excecao()
    demo_contextmanager_decorator()
    demo_with_statement_multiplo()
"""

import time
from contextlib import contextmanager


# ---------------------------------------------------------------------------
# 1. PROTOCOLO __enter__ / __exit__ — na mão, com classe
# ---------------------------------------------------------------------------
# Um context manager é qualquer objeto que implementa dois métodos:
#
#   __enter__(self)                          -> roda ao entrar no `with`,
#                                                o que ele retorna vira o
#                                                valor do `as x`
#   __exit__(self, exc_type, exc_val, exc_tb) -> roda ao SAIR do `with`,
#                                                SEMPRE (com ou sem erro)
#
# É exatamente isso que garante que recursos (arquivos, conexões, locks)
# sejam liberados de forma confiável, mesmo se algo der errado no meio.

class Cronometro:
    def __enter__(self):
        self.inicio = time.perf_counter()
        print("  [entrando: cronômetro iniciado]")
        return self  # isso vira o "as x" do with

    def __exit__(self, exc_type, exc_val, exc_tb):
        fim = time.perf_counter()
        print(f"  [saindo: levou {fim - self.inicio:.6f}s]")
        # return False (ou None) = não engole a exceção, ela continua propagando
        # return True = "abafa" a exceção, o with continua como se nada tivesse acontecido
        return False


def demo_context_manager_classe():
    with Cronometro() as c:
        print("  fazendo algo dentro do with...")
        time.sleep(0.1)
    print("já saiu do with")


# ---------------------------------------------------------------------------
# 2. __exit__ RODA MESMO COM EXCEÇÃO — isso é o ponto principal
# ---------------------------------------------------------------------------
# Isso é o que diferencia um context manager de só rodar código antes/depois
# manualmente: o __exit__ é chamado até quando o código dentro do with
# quebra. É assim que um arquivo aberto com `with open(...)` é fechado
# mesmo se der erro no meio da leitura.

class RecursoComErro:
    def __enter__(self):
        print("  [recurso aberto]")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            print(
                f"  [__exit__ percebeu o erro: {exc_type.__name__}: {exc_val}]")
        print("  [recurso fechado de qualquer forma]")
        return False  # deixa a exceção continuar subindo


def demo_context_manager_com_excecao():
    try:
        with RecursoComErro():
            print("  fazendo algo que vai quebrar...")
            raise ValueError("algo deu errado aqui dentro")
    except ValueError as e:
        print(f"Exceção capturada FORA do with: {e}")
    # repare: mesmo com a exceção, "[recurso fechado de qualquer forma]"
    # apareceu antes do except pegar o erro


# ---------------------------------------------------------------------------
# 3. @contextmanager — a versão com generator (mais enxuta)
# ---------------------------------------------------------------------------
# Em vez de escrever uma classe inteira com __enter__/__exit__, dá pra usar
# uma função geradora: tudo ANTES do yield é o __enter__, o valor do yield
# é o "as x", e tudo DEPOIS do yield é o __exit__.
#
# Se algo der errado dentro do with, a exceção é relançada exatamente no
# ponto do yield — por isso o try/finally é importante aqui.

@contextmanager
def cronometro_simples(nome):
    inicio = time.perf_counter()
    print(f"  [{nome}: iniciado]")
    try:
        yield nome  # tudo antes = __enter__, isso é o "as x"
    finally:
        # tudo depois do yield = __exit__, roda mesmo se der exceção
        fim = time.perf_counter()
        print(f"  [{nome}: levou {fim - inicio:.6f}s]")


def demo_contextmanager_decorator():
    with cronometro_simples("tarefa") as nome:
        print(f"  executando {nome}...")
        time.sleep(0.1)


# ---------------------------------------------------------------------------
# 4. MÚLTIPLOS CONTEXT MANAGERS NO MESMO WITH
# ---------------------------------------------------------------------------
# Dá pra abrir vários de uma vez. A ordem de entrada é da esquerda pra
# direita, e a ordem de saída é o INVERSO (o último que entrou é o
# primeiro que sai — como uma pilha).

@contextmanager
def bloco(nome):
    print(f"  entrando em {nome}")
    yield nome
    print(f"  saindo de {nome}")


def demo_with_statement_multiplo():
    with bloco("A") as a, bloco("B") as b:
        print(f"  dentro dos dois: {a}, {b}")
    # ordem esperada:
    # entrando em A -> entrando em B -> dentro dos dois -> saindo de B -> saindo de A
