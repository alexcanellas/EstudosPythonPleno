"""
ESTRUTURAS DE DADOS INTERNAS — exemplos comentados.

Foco: como list, dict e set funcionam por dentro, e por que isso importa
na hora de escolher qual estrutura usar. Rode no shell:

    from estruturas_dados.exemplos import *
    demo_complexidade_lista()
    demo_dict_hash()
    demo_set_operacoes()
    demo_benchmark_list_vs_set()
"""

import timeit


# ---------------------------------------------------------------------------
# 1. LIST — array dinâmico
# ---------------------------------------------------------------------------
# Por dentro, uma list do Python é um array (bloco contíguo de memória com
# ponteiros pros objetos), com espaço extra reservado (over-allocation) pra
# evitar realocar a cada append. Isso define a complexidade de cada operação:
#
#   lista[i]                -> O(1)      acesso direto por índice
#   lista.append(x)         -> O(1)*     amortizado (às vezes precisa realocar)
#   lista.insert(0, x)      -> O(n)      empurra todo mundo pra direita
#   lista.pop()             -> O(1)      remove do final
#   lista.pop(0)            -> O(n)      remove do início, reorganiza tudo
#   x in lista               -> O(n)      precisa varrer item por item

def demo_complexidade_lista():
    lista = [1, 2, 3, 4, 5]

    print("Acesso por índice (O(1)):", lista[2])

    # append no final é rápido — O(1) amortizado
    lista.append(6)
    print("Depois do append:", lista)

    # insert no início é caro — O(n), porque desloca todos os elementos
    lista.insert(0, 0)
    print("Depois do insert(0):", lista)

    # busca "in" percorre a lista inteira no pior caso — O(n)
    print("5 está na lista?", 5 in lista)


# ---------------------------------------------------------------------------
# 2. DICT — hash table
# ---------------------------------------------------------------------------
# Por dentro, um dict guarda pares (hash da chave -> valor) numa tabela hash.
# Isso é o que permite dict['chave'] ser O(1) em média, em vez de precisar
# varrer tudo como numa lista.
#
# CONSEQUÊNCIA IMPORTANTE: a chave precisa ser hashable (imutável).
# list não pode ser chave de dict (é mutável), mas tuple pode.

class ChaveNaoHashable:
    pass


def demo_dict_hash():
    funcionario = {"nome": "Alexandre", "cargo": "Dev"}

    # acesso por chave -> O(1) médio, não importa o tamanho do dict
    print("Acesso direto:", funcionario["nome"])

    # hash() é o que o dict usa por trás dos panos pra localizar o "balde"
    # (bucket) onde a chave vive
    print("Hash da string 'nome':", hash("nome"))

    # tuple é hashable -> pode ser chave
    coordenadas = {(0, 0): "origem", (1, 1): "diagonal"}
    print("Tupla como chave funciona:", coordenadas[(0, 0)])

    # list NÃO é hashable -> não pode ser chave (list é mutável, hash
    # precisaria mudar se o conteúdo mudasse, o que quebraria a tabela hash)
    try:
        d = {[1, 2]: "erro"}
    except TypeError as e:
        print(f"Erro esperado ao usar list como chave: {e}")


# ---------------------------------------------------------------------------
# 3. SET — mesma hash table do dict, mas só guardando chaves
# ---------------------------------------------------------------------------
# set usa a MESMA estrutura de hash table do dict por baixo (só que sem
# valor associado). Por isso, `x in set` também é O(1) médio — bem
# diferente de `x in list`, que é O(n).

def demo_set_operacoes():
    times_a = {"Flamengo", "Vasco", "Fluminense"}
    times_b = {"Vasco", "Botafogo", "Fluminense"}

    print("União:", times_a | times_b)
    print("Interseção:", times_a & times_b)
    print("Diferença (A - B):", times_a - times_b)

    # busca em set é O(1) médio, independente do tamanho
    print("'Vasco' está no set?", "Vasco" in times_a)


# ---------------------------------------------------------------------------
# 4. BENCHMARK REAL — list vs set na busca "in"
# ---------------------------------------------------------------------------
# Isso não é teoria: dá pra medir a diferença de verdade com timeit.
# Quanto maior a estrutura, mais escancarada fica a diferença O(n) vs O(1).

def demo_benchmark_list_vs_set():
    tamanho = 100_000
    lista = list(range(tamanho))
    conjunto = set(range(tamanho))

    # busca por um elemento que está no FINAL (pior caso pra lista)
    alvo = tamanho - 1

    tempo_lista = timeit.timeit(
        lambda: alvo in lista,
        number=1000
    )
    tempo_set = timeit.timeit(
        lambda: alvo in conjunto,
        number=1000
    )

    print(f"Tamanho da estrutura: {tamanho:,}")
    print(f"Busca em list (O(n)): {tempo_lista:.6f}s para 1000 buscas")
    print(f"Busca em set  (O(1)): {tempo_set:.6f}s para 1000 buscas")
    print(f"Set foi {tempo_lista / tempo_set:.0f}x mais rápido")
