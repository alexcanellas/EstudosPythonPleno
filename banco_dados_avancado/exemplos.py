"""
BANCO DE DADOS AVANÇADO — exemplos comentados.

Reaproveita os models Autor/Livro do django_drf_avancado. Pré-requisito:
rodar `python manage.py popular_dados` antes (mesmo comando de lá).

Rode no shell:

    from banco_dados_avancado.exemplos import *
    demo_sql_puro_vs_orm()
    demo_explain_query_plan()
"""

from django.db import connection
from django_drf_avancado.models import Autor, Livro


# ---------------------------------------------------------------------------
# 1. SQL PURO (via cursor) vs ORM — o mesmo resultado, dois caminhos
# ---------------------------------------------------------------------------
# O ORM existe pra evitar escrever SQL na mão no dia a dia, mas por baixo
# dos panos ele SEMPRE vira SQL. Entender o SQL puro ajuda a "ler" o que
# o ORM está fazendo, e é indispensável pra query complexa demais pro
# ORM expressar bem (ou pra otimizar algo que o ORM não deixa controlar).
#
# connection.cursor() dá acesso direto ao banco, sem passar pelo ORM —
# você escreve SQL cru, exatamente como seria num client de banco.

def demo_sql_puro_vs_orm():
    print("=== JOIN: livros com nome do autor ===\n")

    print("Via ORM (select_related faz JOIN por baixo dos panos):")
    livros_orm = Livro.objects.select_related('autor').all()[:3]
    for livro in livros_orm:
        print(f"  {livro.titulo} — {livro.autor.nome}")

    print("\nO MESMO resultado, via SQL puro:")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT livro.titulo, autor.nome
            FROM django_drf_avancado_livro AS livro
            INNER JOIN django_drf_avancado_autor AS autor
                ON livro.autor_id = autor.id
            LIMIT 3
        """)
        for titulo, nome_autor in cursor.fetchall():
            print(f"  {titulo} — {nome_autor}")

    print("\n=== SUBQUERY: autores que têm livro publicado antes de 1900 ===\n")

    print("Via ORM (subquery escondida dentro do filter):")
    autores_orm = Autor.objects.filter(livros__ano_publicacao__lt=1900).distinct()
    for autor in autores_orm:
        print(f"  {autor.nome}")

    print("\nO MESMO resultado, via SQL puro com subquery explícita:")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT nome
            FROM django_drf_avancado_autor
            WHERE id IN (
                SELECT autor_id
                FROM django_drf_avancado_livro
                WHERE ano_publicacao < 1900
            )
        """)
        for (nome,) in cursor.fetchall():
            print(f"  {nome}")

    print("\n(repare: o ORM escondeu a subquery inteira atrás de "
          "__lt e __, mas o SQL gerado por trás é equivalente ao que "
          "escrevemos na mão)")


# ---------------------------------------------------------------------------
# 2. EXPLAIN QUERY PLAN — como o banco DECIDE executar a query
# ---------------------------------------------------------------------------
# EXPLAIN QUERY PLAN não executa a query de verdade — ele pede pro banco
# explicar a ESTRATÉGIA que usaria: vai varrer a tabela inteira (SCAN,
# lento) ou usar um índice pra pular direto pro dado (SEARCH, rápido)?
# Isso é a ferramenta #1 pra descobrir POR QUE uma query está lenta.

def demo_explain_query_plan():
    print("=== Plano de execução: buscar livro por título ===\n")

    with connection.cursor() as cursor:
        cursor.execute("""
            EXPLAIN QUERY PLAN
            SELECT * FROM django_drf_avancado_livro
            WHERE titulo = 'Dom Casmurro'
        """)
        for linha in cursor.fetchall():
            print(f"  {linha}")

    print("\n(no SQLite, o resultado tem colunas tipo (id, parent, notused, "
          "detail) — o campo 'detail' é o que importa: se aparecer "
          "'SCAN django_drf_avancado_livro', significa que o banco está "
          "varrendo TODAS as linhas da tabela, uma por uma, até achar o "
          "título — porque titulo NÃO tem índice. Se aparecesse 'SEARCH', "
          "significaria que ele usou um índice pra pular direto pro dado)")

    print("\n=== Plano de execução: buscar por id (chave primária) ===\n")

    with connection.cursor() as cursor:
        cursor.execute("""
            EXPLAIN QUERY PLAN
            SELECT * FROM django_drf_avancado_livro
            WHERE id = 1
        """)
        for linha in cursor.fetchall():
            print(f"  {linha}")

    print("\n(esse aqui deve mostrar SEARCH, não SCAN — porque 'id' é "
          "chave primária, e toda chave primária JÁ TEM índice automático. "
          "É por isso que buscar por id é sempre rápido, mesmo em tabelas "
          "gigantes, mas buscar por outro campo sem índice fica cada vez "
          "mais lento conforme a tabela cresce)")


import time




# ---------------------------------------------------------------------------
# 3. ÍNDICES — medindo o ganho de performance de verdade
# ---------------------------------------------------------------------------
# Um índice é uma estrutura auxiliar (geralmente uma B-Tree) que o banco
# mantém ORDENADA, permitindo pular direto pro dado em vez de varrer
# tabela inteira. O custo: todo INSERT/UPDATE fica um pouco mais lento
# (o índice também precisa ser atualizado), e o índice ocupa espaço extra
# em disco. Por isso não se cria índice em TUDO — só nos campos que
# realmente são usados em WHERE/JOIN/ORDER BY com frequência.
#
# Com poucos registros (como os 7 livros que populamos), a diferença é
# imperceptível — o SQLite resolve isso em microssegundos de qualquer
# jeito. Pra ENXERGAR o ganho, essa demo cria uma massa de dados maior
# temporariamente, mede, e depois limpa tudo.

def demo_indice_performance():
    from django_drf_avancado.models import Autor, Livro

    print("Criando massa de dados temporária (50.000 livros)...")
    autor_temp = Autor.objects.create(nome="__TEMP_BENCHMARK__", nacionalidade="Teste")

    # bulk_create insere tudo numa única operação otimizada, bem mais
    # rápido que 50.000 chamadas separadas de .create()
    livros_temp = [
        Livro(
            titulo=f"Livro Temporário {i}",
            autor=autor_temp,
            ano_publicacao=2000,
            preco=10.0,
        )
        for i in range(50_000)
    ]
    Livro.objects.bulk_create(livros_temp)
    print("  Massa de dados criada.\n")

    alvo = "Livro Temporário 49999"  # o último, pior caso pra uma varredura

    print("SEM índice no campo 'titulo':")
    inicio = time.perf_counter()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM django_drf_avancado_livro WHERE titulo = %s",
            [alvo],
        )
        cursor.fetchall()
    tempo_sem_indice = time.perf_counter() - inicio
    print(f"  Tempo: {tempo_sem_indice:.6f}s")

    print("\nCriando índice no campo 'titulo'...")
    with connection.cursor() as cursor:
        cursor.execute(
            "CREATE INDEX idx_temp_titulo ON django_drf_avancado_livro (titulo)"
        )

    print("COM índice no campo 'titulo':")
    inicio = time.perf_counter()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM django_drf_avancado_livro WHERE titulo = %s",
            [alvo],
        )
        cursor.fetchall()
    tempo_com_indice = time.perf_counter() - inicio
    print(f"  Tempo: {tempo_com_indice:.6f}s")

    print(f"\nGanho: {tempo_sem_indice / tempo_com_indice:.0f}x mais rápido")

    # limpeza: remove o índice temporário e os 50.000 livros de teste,
    # pra não deixar sujeira nos outros demos
    print("\nLimpando dados temporários...")
    with connection.cursor() as cursor:
        cursor.execute("DROP INDEX idx_temp_titulo")
    Livro.objects.filter(autor=autor_temp).delete()
    autor_temp.delete()
    print("  Limpeza concluída.")







# ---------------------------------------------------------------------------
# 4. ISOLAMENTO DE TRANSAÇÕES — race condition e select_for_update
# ---------------------------------------------------------------------------
# Isolamento é sobre o que acontece quando DUAS transações mexem no MESMO
# dado ao mesmo tempo. O cenário clássico de entrevista: dois processos
# tentam debitar de um mesmo saldo simultaneamente, e sem proteção, os
# dois podem "ler" o saldo ANTES de qualquer um escrever — resultando em
# saldo incorreto (um debitou, mas achou que ainda tinha o valor original).
#
# select_for_update() resolve isso travando a LINHA no banco: a segunda
# transação que tentar ler o mesmo registro fica ESPERANDO a primeira
# terminar (commit ou rollback), em vez de ler um valor desatualizado.
#
# Esse demo simula o problema (sem select_for_update) e depois a solução
# (com select_for_update), usando o preço de um livro como "saldo".

from django.db import transaction
from decimal import Decimal

def demo_race_condition_sem_protecao():
    from django_drf_avancado.models import Livro

    livro = Livro.objects.first()
    preco_original = livro.preco
    print(f"Preço original: {preco_original}")

    print("\nSIMULANDO race condition (sem select_for_update):")
    print("  Duas 'transações' leem o MESMO preço, cada uma aplica um "
          "desconto de 10%, e salva — sem saber da outra.")

    # transação A: lê o preço
    livro_a = Livro.objects.get(pk=livro.pk)
    print(f"  [Transação A] leu preço: {livro_a.preco}")

    # transação B: lê o MESMO preço, ANTES de A salvar
    livro_b = Livro.objects.get(pk=livro.pk)
    print(f"  [Transação B] leu preço: {livro_b.preco}")

    # transação A aplica desconto e salva
    livro_a.preco = livro_a.preco * Decimal("0.9")
    livro_a.save()
    print(f"  [Transação A] salvou novo preço: {livro_a.preco}")

    # transação B aplica desconto EM CIMA DO VALOR QUE ELA LEU (desatualizado!)
    # e sobrescreve o que A acabou de salvar
    livro_b.preco = livro_b.preco * Decimal("0.9")
    livro_b.save()
    print(f"  [Transação B] salvou novo preço: {livro_b.preco}")

    livro.refresh_from_db()
    preco_esperado_com_dois_descontos = round(preco_original * Decimal("0.9") * Decimal("0.9"), 2)
    print(f"\nPreço final no banco: {livro.preco}")
    print(f"Preço esperado se os DOIS descontos tivessem aplicado corretamente: "
          f"{preco_esperado_com_dois_descontos}")
    print("(no SQLite local isso pode não divergir de forma visível, porque "
          "as operações são rápidas demais pra 'colidir' de verdade — mas em "
          "um banco sob carga real, com muitas conexões simultâneas, essa é "
          "EXATAMENTE a race condition que causa preços/saldos errados em "
          "produção)")

    # restaura o preço original, pra não deixar sujeira nos outros demos
    livro.preco = preco_original
    livro.save()


def demo_select_for_update():
    from django_drf_avancado.models import Livro

    livro = Livro.objects.first()
    preco_original = livro.preco

    print("COM select_for_update (a forma correta):")
    with transaction.atomic():
        # select_for_update() trava a LINHA no banco até essa transação
        # terminar (commit ou rollback). Qualquer outra transação que
        # tentar dar select_for_update() nessa MESMA linha fica esperando.
        livro_travado = Livro.objects.select_for_update().get(pk=livro.pk)
        print(f"  Linha travada, preço lido: {livro_travado.preco}")

        livro_travado.preco = livro_travado.preco * Decimal("0.9")
        livro_travado.save()
        print(f"  Novo preço salvo: {livro_travado.preco}")
        # a trava é liberada automaticamente quando o bloco `atomic`
        # termina (aqui, no fim do `with`)

    print("\n(nesse ponto, se outra transação estivesse esperando pra "
          "mexer nessa mesma linha, ela só conseguiria prosseguir AGORA, "
          "já vendo o preço atualizado — nunca o valor desatualizado)")

    livro.refresh_from_db()
    livro.preco = preco_original
    livro.save()
    print(f"\nPreço restaurado ao original: {livro.preco}")