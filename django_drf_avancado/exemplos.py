"""
DJANGO/DRF AVANÇADO — ORM: N+1, select_related, prefetch_related, transactions.

Pré-requisito: rodar `python manage.py popular_dados` antes (senão as
demos não têm dados pra consultar).

Rode no shell:

    from django_drf_avancado.exemplos import *
    demo_problema_n_mais_1()
    demo_solucao_select_related()
    demo_prefetch_related()
    demo_transaction_atomic()
"""

from django.db import transaction
from django.test.utils import CaptureQueriesContext
from django.db import connection

from django_drf_avancado.models import Autor, Livro


# ---------------------------------------------------------------------------
# 1. O PROBLEMA N+1 — provado com contagem real de queries
# ---------------------------------------------------------------------------
# Sem otimização, buscar N livros e acessar o autor de cada um dispara:
#   1 query pra buscar os livros
#   + N queries, uma pra cada autor.livro (uma consulta por acesso)
# = N+1 queries no total, quando poderia ser só 1 ou 2.
#
# CaptureQueriesContext registra TODAS as queries SQL executadas dentro
# do bloco `with`, independente de DEBUG estar ligado ou não.

def demo_problema_n_mais_1():
    with CaptureQueriesContext(connection) as contexto:
        livros = Livro.objects.all()  # ainda não bateu no banco (lazy)
        for livro in livros:
            # aqui SIM bate no banco: 1 query pra pegar a lista de livros,
            # e mais 1 query TODA VEZ que acessa livro.autor pela primeira
            # vez (o Django não sabe de antemão que você vai precisar do
            # autor, então busca sob demanda)
            print(f"  {livro.titulo} — {livro.autor.nome}")

    print(f"\nTotal de queries executadas: {len(contexto.captured_queries)}")
    print("(esperado: 1 query dos livros + 1 query POR autor acessado — "
          "isso é o N+1)")


# ---------------------------------------------------------------------------
# 2. SOLUÇÃO: select_related — JOIN no SQL
# ---------------------------------------------------------------------------
# select_related() faz um JOIN SQL e traz o autor JUNTO na mesma query.
# Usa isso pra relacionamentos "para um" (ForeignKey, OneToOne) — o
# oposto de prefetch_related, que é pra relacionamentos "para muitos".

def demo_solucao_select_related():
    with CaptureQueriesContext(connection) as contexto:
        livros = Livro.objects.select_related('autor').all()
        for livro in livros:
            # aqui NÃO dispara query nova — o autor já veio junto no JOIN
            print(f"  {livro.titulo} — {livro.autor.nome}")

    print(f"\nTotal de queries executadas: {len(contexto.captured_queries)}")
    print("(esperado: 1 única query, com JOIN — resolveu o N+1)")


# ---------------------------------------------------------------------------
# 3. prefetch_related — pra relacionamentos "para muitos"
# ---------------------------------------------------------------------------
# Ao contrário do select_related (JOIN numa query só), prefetch_related
# faz uma SEGUNDA query separada, buscando TODOS os relacionados de uma
# vez, e depois o Django "junta" tudo em memória (Python), em vez de SQL.
# É a escolha certa quando o relacionamento é reverso ou muitos-pra-muitos
# (aqui: um autor tem VÁRIOS livros — autor.livros.all()).

def demo_prefetch_related():
    print("SEM prefetch_related (N+1 na direção reversa):")
    with CaptureQueriesContext(connection) as contexto:
        autores = Autor.objects.all()
        for autor in autores:
            qtd_livros = autor.livros.count()  # 1 query por autor
            print(f"  {autor.nome}: {qtd_livros} livro(s)")
    print(f"  Total de queries: {len(contexto.captured_queries)}\n")

    print("COM prefetch_related:")
    with CaptureQueriesContext(connection) as contexto:
        autores = Autor.objects.prefetch_related('livros').all()
        for autor in autores:
            qtd_livros = autor.livros.count()  # já veio pré-carregado, sem nova query
            print(f"  {autor.nome}: {qtd_livros} livro(s)")
    print(f"  Total de queries: {len(contexto.captured_queries)}")
    print("  (esperado: 2 queries no total — 1 pros autores, 1 pra TODOS "
          "os livros de uma vez — independente de quantos autores existam)")


# ---------------------------------------------------------------------------
# 4. transaction.atomic — tudo ou nada
# ---------------------------------------------------------------------------
# Um bloco atomic garante que TODAS as operações dentro dele acontecem,
# ou NENHUMA acontece (rollback automático se der erro no meio). Essencial
# pra operações que envolvem múltiplas escritas relacionadas — ex: criar
# um pedido E debitar estoque ao mesmo tempo.

def demo_transaction_atomic():
    total_antes = Autor.objects.count()
    print(f"Total de autores ANTES: {total_antes}")

    try:
        with transaction.atomic():
            Autor.objects.create(nome="Autor Temporário",
                                 nacionalidade="Teste")
            print("  Autor temporário criado dentro do bloco atomic...")

            # simula um erro no MEIO da transação
            raise ValueError("Algo deu errado depois de criar o autor!")

    except ValueError as e:
        print(f"  Exceção capturada: {e}")

    total_depois = Autor.objects.count()
    print(f"Total de autores DEPOIS: {total_depois}")
    print("(esperado: os dois números são IGUAIS — o rollback desfez a "
          "criação do autor temporário, porque o erro aconteceu dentro "
          "do bloco atomic)")
