"""
DECORATORS — exemplos comentados.

Foco: como um decorator funciona por baixo dos panos, decorators com
argumentos, functools.wraps e o problema que ele resolve, e decorators
empilhados. Rode no shell:

    from decorators.exemplos import *
    demo_decorator_simples()
    demo_sem_wraps_vs_com_wraps()
    demo_decorator_com_argumentos()
    demo_decorators_empilhados()
"""

import functools
import time


# ---------------------------------------------------------------------------
# 1. DECORATOR SIMPLES — o que a sintaxe @ realmente faz
# ---------------------------------------------------------------------------
# Um decorator é só uma função que recebe outra função e devolve uma nova
# função "envolvendo" ela. A sintaxe @decorator é açúcar sintático pra:
#
#   def minha_funcao(): ...
#   minha_funcao = decorator(minha_funcao)

def cronometro(func):
    @functools.wraps(func)  # ver demo_sem_wraps_vs_com_wraps() sobre isso
    def wrapper(*args, **kwargs):
        inicio = time.perf_counter()
        resultado = func(*args, **kwargs)
        fim = time.perf_counter()
        print(f"  [{func.__name__} levou {fim - inicio:.6f}s]")
        return resultado
    return wrapper


@cronometro
def soma_lenta(a, b):
    time.sleep(0.1)
    return a + b


def demo_decorator_simples():
    # isso é EXATAMENTE o mesmo que:
    #   soma_lenta_original = soma_lenta
    #   soma_lenta = cronometro(soma_lenta_original)
    resultado = soma_lenta(2, 3)
    print("Resultado:", resultado)


# ---------------------------------------------------------------------------
# 2. O PROBLEMA QUE functools.wraps RESOLVE
# ---------------------------------------------------------------------------
# Sem @functools.wraps, o wrapper "rouba a identidade" da função original:
# __name__, __doc__, etc passam a apontar pro wrapper, não pra função real.
# Isso quebra introspecção, debugging e ferramentas que dependem disso
# (como o admin do Django, ou geradores de documentação automática).

def decorator_sem_wraps(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper  # <- não preserva __name__/__doc__ da função original


def decorator_com_wraps(func):
    @functools.wraps(func)  # <- copia __name__, __doc__, etc pro wrapper
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


@decorator_sem_wraps
def funcao_a():
    """Docstring original da função A."""
    pass


@decorator_com_wraps
def funcao_b():
    """Docstring original da função B."""
    pass


def demo_sem_wraps_vs_com_wraps():
    print("SEM functools.wraps:")
    print(f"  __name__ virou: {funcao_a.__name__}")     # 'wrapper' (errado!)
    print(f"  __doc__ virou: {funcao_a.__doc__}")        # None (perdeu a docstring)

    print("\nCOM functools.wraps:")
    print(f"  __name__ continua: {funcao_b.__name__}")   # 'funcao_b' (correto)
    print(f"  __doc__ continua: {funcao_b.__doc__}")      # docstring preservada


# ---------------------------------------------------------------------------
# 3. DECORATOR COM ARGUMENTOS — uma função que gera decorators
# ---------------------------------------------------------------------------
# Quando você quer @decorator(algum_parametro), precisa de mais um nível
# de aninhamento: uma função que RECEBE o parâmetro e DEVOLVE o decorator
# de verdade.
#
#   @repetir(3)              equivale a:
#   def funcao(): ...          funcao = repetir(3)(funcao)
#
# repetir(3) roda primeiro e devolve o decorator real, que só então
# recebe a função.

def repetir(vezes):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            resultados = []
            for i in range(vezes):
                resultados.append(func(*args, **kwargs))
            return resultados
        return wrapper
    return decorator


@repetir(3)
def saudacao(nome):
    return f"Olá, {nome}!"


def demo_decorator_com_argumentos():
    print(saudacao("Alexandre"))


# ---------------------------------------------------------------------------
# 4. DECORATORS EMPILHADOS — ordem de execução
# ---------------------------------------------------------------------------
# Quando você empilha vários decorators, eles são aplicados de BAIXO PRA
# CIMA (o mais próximo da função roda primeiro), mas EXECUTADOS de CIMA
# PRA BAIXO na hora de chamar a função.
#
#   @decorator_a
#   @decorator_b
#   def funcao(): ...
#
# equivale a: funcao = decorator_a(decorator_b(funcao))
# ou seja: decorator_b "envolve" primeiro, decorator_a envolve por fora.

def log_entrada(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"  -> entrando em {func.__name__}")
        resultado = func(*args, **kwargs)
        print(f"  <- saindo de {func.__name__}")
        return resultado
    return wrapper


def log_maiusculo(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"  [maiusculo] antes de {func.__name__}")
        resultado = func(*args, **kwargs)
        print(f"  [maiusculo] depois de {func.__name__}")
        return resultado
    return wrapper


@log_entrada
@log_maiusculo
def processar(texto):
    return texto.upper()


def demo_decorators_empilhados():
    # ordem de aplicação (de baixo pra cima): log_maiusculo envolve primeiro,
    # log_entrada envolve por fora
    # ordem de EXECUÇÃO (de cima pra baixo): log_entrada roda primeiro
    resultado = processar("python")
    print("Resultado final:", resultado)