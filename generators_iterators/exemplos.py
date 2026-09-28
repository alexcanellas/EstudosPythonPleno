"""
GENERATORS E ITERATORS — exemplos comentados.

Foco: diferença entre iterable e iterator, yield, yield from, e por que
generators economizam memória. Rode no shell:

    from generators_iterators.exemplos import *
    demo_generator_basico()
    demo_memoria_generator_vs_lista()
    demo_yield_from()
    demo_protocolo_iterator()
"""

import sys


# ---------------------------------------------------------------------------
# 1. GENERATOR BÁSICO — yield
# ---------------------------------------------------------------------------
# Uma função normal roda inteira e devolve UM valor com `return`.
# Uma função com `yield` vira um "generator function": cada chamada de
# yield PAUSA a execução e devolve um valor, guardando o estado interno
# (variáveis locais, posição no código) até a próxima chamada de next().

def contador_ate(limite):
    print("  [generator iniciado]")
    n = 1
    while n <= limite:
        yield n          # pausa aqui, devolve `n`, espera o próximo next()
        n += 1
    print("  [generator terminou]")


def demo_generator_basico():
    gen = contador_ate(3)
    print("Objeto criado (nada rodou ainda):", gen)

    # cada next() RETOMA de onde parou, não recomeça do zero
    print("1ª chamada:", next(gen))
    print("2ª chamada:", next(gen))
    print("3ª chamada:", next(gen))

    try:
        next(gen)  # não tem mais valores -> StopIteration
    except StopIteration:
        print("4ª chamada: StopIteration (generator esgotado)")

    # forma mais comum de consumir: for loop (ele trata o StopIteration sozinho)
    print("\nConsumindo com for:")
    for valor in contador_ate(3):
        print(" ", valor)


# ---------------------------------------------------------------------------
# 2. MEMÓRIA: GENERATOR vs LIST COMPREHENSION
# ---------------------------------------------------------------------------
# List comprehension [x for x in ...] cria TODOS os elementos na memória
# de uma vez. Generator expression (x for x in ...) cria só o "gerador" —
# os valores são calculados um de cada vez, sob demanda (lazy evaluation).
#
# Isso importa MUITO quando você está lidando com volumes grandes de dados
# (ex: processar um arquivo de milhões de linhas) — você não precisa ter
# tudo na memória ao mesmo tempo.

def demo_memoria_generator_vs_lista():
    tamanho = 1_000_000

    lista = [x * 2 for x in range(tamanho)]          # calcula TUDO agora
    gerador = (x * 2 for x in range(tamanho))         # não calcula nada ainda

    tam_lista = sys.getsizeof(lista)
    tam_gerador = sys.getsizeof(gerador)

    print(f"Tamanho da list comprehension:      {tam_lista:,} bytes")
    print(f"Tamanho da generator expression:    {tam_gerador:,} bytes")
    print(f"A lista ocupa {tam_lista / tam_gerador:.0f}x mais memória")

    # o generator só entrega os valores quando você pede (ex: no for, ou next())
    print("\nPrimeiros 3 valores do gerador (calculados agora, sob demanda):")
    for i, valor in enumerate(gerador):
        if i >= 3:
            break
        print(" ", valor)


# ---------------------------------------------------------------------------
# 3. YIELD FROM — delegar pra outro generator/iterable
# ---------------------------------------------------------------------------
# `yield from` delega a produção de valores pra outro iterável, evitando
# um for + yield manual. Muito útil pra "achatar" estruturas aninhadas
# ou compor generators.

def generator_pares(ate):
    for n in range(0, ate, 2):
        yield n


def generator_impares(ate):
    for n in range(1, ate, 2):
        yield n


def generator_combinado(ate):
    # sem yield from, seria:
    #   for p in generator_pares(ate): yield p
    #   for i in generator_impares(ate): yield i
    yield from generator_pares(ate)
    yield from generator_impares(ate)


def demo_yield_from():
    print("Combinando dois generators com yield from:")
    print(list(generator_combinado(6)))  # [0, 2, 4, 1, 3, 5]

    # yield from também é ótimo pra achatar listas aninhadas
    def achatar(lista_de_listas):
        for sublista in lista_de_listas:
            yield from sublista

    aninhada = [[1, 2], [3, 4], [5]]
    print("Achatando lista aninhada:", list(achatar(aninhada)))


# ---------------------------------------------------------------------------
# 4. PROTOCOLO ITERATOR — __iter__ e __next__
# ---------------------------------------------------------------------------
# Por baixo dos panos, é isso que faz o `for` funcionar em QUALQUER objeto:
#   - __iter__(self)  -> deve devolver um iterator (geralmente self mesmo)
#   - __next__(self)  -> devolve o próximo valor, ou levanta StopIteration
#
# Um generator (função com yield) já implementa esse protocolo pra você
# automaticamente. Mas dá pra fazer na mão também, e entender isso ajuda
# a entender o que o `yield` está "escondendo".

class Contagem:
    """Iterator escrito na mão, sem usar yield — equivalente ao contador_ate()."""

    def __init__(self, limite):
        self.limite = limite
        self.atual = 0

    def __iter__(self):
        # o próprio objeto é o iterator
        return self

    def __next__(self):
        if self.atual >= self.limite:
            raise StopIteration
        self.atual += 1
        return self.atual


def demo_protocolo_iterator():
    print("Iterator escrito na mão (sem yield):")
    for valor in Contagem(3):
        print(" ", valor)

    # o que o for faz por baixo dos panos, manualmente:
    print("\nO mesmo, chamando __iter__/__next__ na mão:")
    obj = Contagem(3)
    it = iter(obj)          # chama obj.__iter__()
    while True:
        try:
            valor = next(it)   # chama it.__next__()
            print(" ", valor)
        except StopIteration:
            break