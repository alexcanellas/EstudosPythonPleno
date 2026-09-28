"""
CONCORRÊNCIA — exemplos comentados.

Foco: o GIL, e por que threading/multiprocessing/asyncio se comportam
diferente dependendo do tipo de tarefa (CPU-bound vs I/O-bound).
Rode no shell:

    from concorrencia.exemplos import *
    demo_gil_threading_cpu_bound()
    demo_multiprocessing_cpu_bound()
    demo_threading_io_bound()
    demo_asyncio_io_bound()

IMPORTANTE: cada demo pode levar alguns segundos pra rodar (é proposital,
pra dar pra medir e comparar tempo de verdade).
"""

import time
import threading
import multiprocessing
import asyncio


# ---------------------------------------------------------------------------
# O GIL (Global Interpreter Lock), resumido:
# ---------------------------------------------------------------------------
# O CPython (a implementação padrão do Python) tem um lock global que
# garante que só UMA thread executa bytecode Python por vez, mesmo que
# você tenha várias threads rodando "ao mesmo tempo". Isso significa:
#
#   - Tarefa CPU-bound (cálculo pesado)     -> threading NÃO ajuda,
#                                               porque só uma thread roda
#                                               por vez de qualquer jeito
#   - Tarefa I/O-bound (esperar rede/disco) -> threading AJUDA, porque o
#                                               GIL é LIBERADO durante a
#                                               espera de I/O
#
# multiprocessing contorna o GIL de vez, porque cada processo tem seu
# próprio interpretador Python (e seu próprio GIL) — mas tem custo de
# criar processos e não compartilha memória facilmente.
#
# asyncio não usa threads nem processos: é UMA thread só, mas que troca
# de tarefa cooperativamente sempre que uma tarefa "dá um await" (avisa
# "pode ir fazer outra coisa enquanto eu espero").


# ---------------------------------------------------------------------------
# 1. TAREFA CPU-BOUND — cálculo pesado, sem esperar nada externo
# ---------------------------------------------------------------------------
def tarefa_cpu_bound(n):
    """Trabalho de CPU de verdade: soma de quadrados até n."""
    return sum(i * i for i in range(n))


def demo_gil_threading_cpu_bound():
    N = 20_000_000

    # SEQUENCIAL: roda as duas chamadas uma depois da outra
    inicio = time.perf_counter()
    tarefa_cpu_bound(N)
    tarefa_cpu_bound(N)
    tempo_sequencial = time.perf_counter() - inicio
    print(f"Sequencial (sem threads):  {tempo_sequencial:.2f}s")

    # THREADING: duas threads "ao mesmo tempo"
    inicio = time.perf_counter()
    t1 = threading.Thread(target=tarefa_cpu_bound, args=(N,))
    t2 = threading.Thread(target=tarefa_cpu_bound, args=(N,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    tempo_threading = time.perf_counter() - inicio
    print(f"Com threading:              {tempo_threading:.2f}s")

    print(f"\nGanho: {tempo_sequencial / tempo_threading:.2f}x "
          f"(esperado: próximo de 1x, ou seja, quase NENHUM ganho — "
          f"o GIL não deixa as threads rodarem CPU em paralelo de verdade)")


# ---------------------------------------------------------------------------
# 2. A MESMA TAREFA CPU-BOUND, AGORA COM MULTIPROCESSING
# ---------------------------------------------------------------------------
def demo_multiprocessing_cpu_bound():
    N = 20_000_000

    inicio = time.perf_counter()
    tarefa_cpu_bound(N)
    tarefa_cpu_bound(N)
    tempo_sequencial = time.perf_counter() - inicio
    print(f"Sequencial (sem processos): {tempo_sequencial:.2f}s")

    inicio = time.perf_counter()
    with multiprocessing.Pool(processes=2) as pool:
        pool.map(tarefa_cpu_bound, [N, N])
    tempo_multiprocessing = time.perf_counter() - inicio
    print(f"Com multiprocessing:        {tempo_multiprocessing:.2f}s")

    print(f"\nGanho: {tempo_sequencial / tempo_multiprocessing:.2f}x "
          f"(esperado: próximo de 2x — cada processo tem seu próprio GIL, "
          f"então roda de verdade em paralelo, aproveitando os núcleos da CPU)")


# ---------------------------------------------------------------------------
# 3. TAREFA I/O-BOUND — esperar algo externo (aqui simulado com sleep)
# ---------------------------------------------------------------------------
# time.sleep() aqui representa qualquer espera de I/O real: uma requisição
# HTTP, uma query no banco, leitura de um arquivo grande em disco, etc.
# O ponto chave: durante um I/O real, o SISTEMA OPERACIONAL é quem está
# esperando, não a CPU — e o Python LIBERA o GIL nesse momento, permitindo
# outra thread rodar enquanto isso.

def tarefa_io_bound(segundos):
    time.sleep(segundos)
    return f"esperei {segundos}s"


def demo_threading_io_bound():
    ESPERA = 1  # 1 segundo por tarefa, 4 tarefas

    # SEQUENCIAL: 4 esperas de 1s, uma atrás da outra = ~4s
    inicio = time.perf_counter()
    for _ in range(4):
        tarefa_io_bound(ESPERA)
    tempo_sequencial = time.perf_counter() - inicio
    print(f"Sequencial (sem threads):  {tempo_sequencial:.2f}s")

    # THREADING: 4 threads esperando ao mesmo tempo = ~1s (não ~4s)
    inicio = time.perf_counter()
    threads = [threading.Thread(target=tarefa_io_bound, args=(ESPERA,)) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    tempo_threading = time.perf_counter() - inicio
    print(f"Com threading:              {tempo_threading:.2f}s")

    print(f"\nGanho: {tempo_sequencial / tempo_threading:.2f}x "
          f"(esperado: próximo de 4x — aqui o GIL não atrapalha, porque "
          f"threads em I/O passam a maior parte do tempo esperando, não "
          f"disputando CPU)")


# ---------------------------------------------------------------------------
# 4. A MESMA TAREFA I/O-BOUND, AGORA COM ASYNCIO
# ---------------------------------------------------------------------------
# asyncio resolve o mesmo problema que threading resolve pra I/O-bound,
# mas com UMA thread só, trocando de tarefa nos pontos de `await`. Como
# não precisa criar threads (mais leve) nem lidar com lock/race condition
# entre elas, costuma ser a escolha preferida hoje em dia pra I/O-bound
# em Python (ex: FastAPI é construído em cima disso).

async def tarefa_io_bound_async(segundos):
    await asyncio.sleep(segundos)  # libera o "loop" pra rodar outra tarefa
    return f"esperei {segundos}s"


async def _rodar_asyncio_io_bound():
    ESPERA = 1
    # asyncio.gather roda as 4 corrotinas "ao mesmo tempo" numa única thread
    await asyncio.gather(*[tarefa_io_bound_async(ESPERA) for _ in range(4)])


def demo_asyncio_io_bound():
    ESPERA = 1

    inicio = time.perf_counter()
    for _ in range(4):
        time.sleep(ESPERA)
    tempo_sequencial = time.perf_counter() - inicio
    print(f"Sequencial (sem asyncio):  {tempo_sequencial:.2f}s")

    inicio = time.perf_counter()
    asyncio.run(_rodar_asyncio_io_bound())
    tempo_asyncio = time.perf_counter() - inicio
    print(f"Com asyncio:                {tempo_asyncio:.2f}s")

    print(f"\nGanho: {tempo_sequencial / tempo_asyncio:.2f}x "
          f"(esperado: próximo de 4x, igual o threading — mas com UMA "
          f"thread só, sem overhead de criar/gerenciar threads)")