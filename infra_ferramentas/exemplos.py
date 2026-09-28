"""
INFRA E FERRAMENTAS: variáveis de ambiente e segredos.

Rode no shell:

    from infra_ferramentas.exemplos import *
    demo_leitura_com_tipos()
    demo_ordem_de_prioridade()
    demo_variavel_obrigatoria_ausente()
    demo_mascarar_segredo()
"""

import os 
from decouple import config, Csv, UndefinedValueError
import time
from django.core.cache import cache

import shutil
import stat
import subprocess
from pathlib import Path
import tempfile

# ---------------------------------------------------------------------------
# 1. TUDO NO AMBIENTE É TEXTO: o cast faz a conversão
# ---------------------------------------------------------------------------
# Variável de ambiente é sempre string. O erro clássico é usar o valor
# cru: bool("False") é True, porque qualquer string não vazia é truthy.

def demo_leitura_com_tipos():
    cru = config('DEBUG')                   # sem cast: string
    convertido = config('DEBUG', cast=bool)  # com cast: bool de verdade

    print(f"Sem cast:  {cru!r}  (tipo: {type(cru).__name__})")
    print(f"Com cast:  {convertido!r}  (tipo: {type(convertido).__name__})")

    print(
        f"\nbool('False') = {bool('False')}  <- a armadilha: string não vazia é True")

    hosts = config('ALLOWED_HOSTS', cast=Csv())
    print(f"\nCsv(): {hosts}  (tipo: {type(hosts).__name__})")


# ---------------------------------------------------------------------------
# 2. ORDEM DE PRIORIDADE: quem ganha quando o valor existe em vários lugares
# ---------------------------------------------------------------------------
# O decouple procura nesta ordem:
#   1) variável de ambiente REAL do sistema (os.environ)
#   2) arquivo .env
#   3) o default passado no código
# É isso que permite, em produção, sobrescrever o .env sem editar arquivo:
# o servidor define a variável e ela vence.

def demo_ordem_de_prioridade():
    print(f"Só com o .env:               {config('DEMO_PRIORIDADE')}")

    os.environ['DEMO_PRIORIDADE'] = 'vindo do ambiente real'
    try:
        print(f"Com a variável no ambiente:  {config('DEMO_PRIORIDADE')}")
    finally:
        # limpa, pra não sujar o resto da sessão
        del os.environ['DEMO_PRIORIDADE']

    print(f"Depois de limpar:            {config('DEMO_PRIORIDADE')}")

    print(
        f"\nInexistente com default:     {config('NAO_EXISTE', default='valor-padrao')}")


# ---------------------------------------------------------------------------
# 3. FALHAR CEDO: variável obrigatória ausente
# ---------------------------------------------------------------------------
# Sem default, a ausência vira erro imediato e explícito. O oposto (um
# os.environ.get() que devolve None) faz o bug aparecer lá na frente,
# longe da causa: uma conexão que não abre, um token vazio na requisição.

def demo_variavel_obrigatoria_ausente():
    try:
        config('SENHA_DO_BANCO')  # não existe e não tem default
    except UndefinedValueError as erro:
        print(f"Falhou cedo, como esperado: {erro}")

    print(
        f"\nO get() do os.environ devolve: {os.environ.get('SENHA_DO_BANCO')!r}")
    print("(None silencioso: o problema só estouraria mais adiante)")


# ---------------------------------------------------------------------------
# 4. NUNCA IMPRIMIR SEGREDO COMPLETO (log, print, mensagem de erro)
# ---------------------------------------------------------------------------
# Log costuma ser guardado, copiado e compartilhado. Se precisar confirmar
# que um segredo foi carregado, mostre só o começo.

def mascarar(segredo, visiveis=4):
    return segredo[:visiveis] + '*' * 8


def demo_mascarar_segredo():
    from django.conf import settings

    print(f"SECRET_KEY carregada (mascarada): {mascarar(settings.SECRET_KEY)}")
    print(f"Tamanho: {len(settings.SECRET_KEY)} caracteres")


# ---------------------------------------------------------------------------
# 5. CACHE: OPERAÇÕES BÁSICAS
# ---------------------------------------------------------------------------
# get devolve None (ou o default) quando a chave não existe: cache
# ausente nunca é erro, é só um "miss".

def demo_operacoes_basicas():
    cache.set('chave', {'a': 1}, timeout=30)  # expira em 30s
    print("get existente:     ", cache.get('chave'))
    print("get inexistente:   ", cache.get('inexistente'))
    print("get com default:   ", cache.get('inexistente', 'padrão'))

    # get_or_set: se não existir, calcula, guarda e devolve, tudo numa chamada
    valor = cache.get_or_set('calculado', lambda: 6 * 7, timeout=30)
    print("get_or_set:        ", valor)

    cache.delete('chave')
    cache.delete('calculado')
    print("depois do delete:  ", cache.get('chave'))


# ---------------------------------------------------------------------------
# 6. CACHE-ASIDE: o padrão principal
# ---------------------------------------------------------------------------
# BANCO_FALSO faz o papel da fonte de verdade, e buscar_no_banco simula
# uma consulta lenta com sleep. Assim a demo não depende de dados no banco
# e a diferença de tempo fica visível.

BANCO_FALSO = {1: {'titulo': 'Dom Casmurro', 'preco': 29.90}}


def buscar_no_banco(livro_id):
    time.sleep(1)  # simula uma query cara
    return dict(BANCO_FALSO[livro_id])


def buscar_livro_com_cache(livro_id):
    # Convenção de chave: "entidade:id". Deixa claro o que é cada chave
    # e facilita invalidar tudo de uma entidade.
    chave = f'livro:{livro_id}'

    dado = cache.get(chave)
    if dado is not None:
        return dado, 'HIT'

    # MISS: vai na fonte de verdade e guarda pro próximo.
    # `is not None` (e não `if dado:`) porque um resultado legítimo como
    # {} ou 0 é falsy e seria tratado como miss por engano.
    dado = buscar_no_banco(livro_id)
    cache.set(chave, dado, timeout=60)
    return dado, 'MISS'


def demo_cache_aside():
    cache.delete('livro:1')  # garante que a primeira chamada seja miss

    for tentativa in (1, 2, 3):
        inicio = time.perf_counter()
        dado, resultado = buscar_livro_com_cache(1)
        duracao = time.perf_counter() - inicio
        print(f"Tentativa {tentativa}: {resultado:4} em {duracao:.4f}s -> {dado}")


# ---------------------------------------------------------------------------
# 7. INVALIDAÇÃO: o problema difícil do cache
# ---------------------------------------------------------------------------
# Quando a fonte muda e o cache não é avisado, ele continua servindo o
# dado antigo até o timeout. A forma mais comum de resolver é invalidar
# (apagar a chave) no momento da escrita: o próximo acesso vira miss e
# recarrega o dado atualizado.

def atualizar_preco(livro_id, novo_preco, invalidar):
    BANCO_FALSO[livro_id]['preco'] = novo_preco
    if invalidar:
        cache.delete(f'livro:{livro_id}')


def demo_invalidacao():
    preco_original = BANCO_FALSO[1]['preco']
    try:
        cache.delete('livro:1')
        buscar_livro_com_cache(1)  # popula o cache com o preço original
        print(f"Cache populado com preço {preco_original}\n")

        atualizar_preco(1, 99.90, invalidar=False)
        dado, resultado = buscar_livro_com_cache(1)
        print(f"SEM invalidar: {resultado}, lido = {dado['preco']}, "
              f"banco = {BANCO_FALSO[1]['preco']}  <- dado velho")

        atualizar_preco(1, 99.90, invalidar=True)
        dado, resultado = buscar_livro_com_cache(1)
        print(f"COM invalidar: {resultado}, lido = {dado['preco']}, "
              f"banco = {BANCO_FALSO[1]['preco']}  <- atualizado")
    finally:
        # restaura o estado original pra não sujar as próximas demos
        BANCO_FALSO[1]['preco'] = preco_original
        cache.delete('livro:1')


# ---------------------------------------------------------------------------
# 8. TTL (timeout): a rede de segurança
# ---------------------------------------------------------------------------
# Toda chave deveria ter um TTL. Se uma invalidação for esquecida em algum
# lugar, o dado velho ao menos tem prazo de validade. O timeout define
# quanto tempo de defasagem você aceita.

def demo_ttl():
    cache.set('temporario', 'valor', timeout=1)
    print("Logo depois do set:", cache.get('temporario'))
    time.sleep(1.5)
    print("Após 1.5s:         ", cache.get('temporario'))




# ---------------------------------------------------------------------------
# 9. GIT: MERGE vs REBASE E CONFLITOS (em repositórios de treino descartáveis)
# ---------------------------------------------------------------------------
# Tudo acontece dentro da pasta temporária do sistema. Nada aqui encosta
# no repositório do seu projeto.

def _git(pasta, *args):
    """Roda um comando git dentro de `pasta` e devolve o resultado.

    Os -c definem o autor só para esta chamada, então a demo não depende
    da sua configuração global do git e também não a altera.
    """
    return subprocess.run(
        ['git', '-c', 'user.name=Estudos', '-c', 'user.email=estudos@exemplo.com', *args],
        cwd=pasta,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
    )


def _commit(pasta, arquivo, conteudo, mensagem):
    (Path(pasta) / arquivo).write_text(conteudo, encoding='utf-8', newline='\n')
    _git(pasta, 'add', arquivo)
    _git(pasta, 'commit', '-m', mensagem)


def _forcar_remocao(funcao, caminho, _erro):
    # No Windows, os arquivos internos do .git são somente leitura e o
    # rmtree falha neles. Liberamos a escrita e tentamos de novo.
    os.chmod(caminho, stat.S_IWRITE)
    funcao(caminho)


def _pasta_de_treino(nome):
    """Cria (ou recria do zero) um repositório vazio na pasta temporária."""
    pasta = Path(tempfile.gettempdir()) / nome
    if pasta.exists():
        shutil.rmtree(pasta, onexc=_forcar_remocao)
    pasta.mkdir(parents=True)
    _git(pasta, 'init', '-b', 'main')
    return pasta


def _historia_divergente(pasta):
    """main e feature saem do mesmo ponto e cada uma ganha commits próprios."""
    _commit(pasta, 'app.txt', 'base\n', 'commit inicial')

    _git(pasta, 'checkout', '-b', 'feature')
    _commit(pasta, 'login.txt', 'login\n', 'feature: tela de login')
    _commit(pasta, 'logout.txt', 'logout\n', 'feature: botao de logout')

    _git(pasta, 'checkout', 'main')
    _commit(pasta, 'hotfix.txt', 'fix\n', 'hotfix: corrige bug em producao')


def _grafico(pasta):
    return _git(pasta, 'log', '--graph', '--oneline', '--decorate', '--all').stdout


# --- merge vs rebase --------------------------------------------------------
# Partindo do MESMO ponto de partida, a mesma divergência é integrada de
# dois jeitos, e o desenho do histórico é o que muda.
#
#   merge  -> preserva o histórico como aconteceu e cria um commit de merge
#   rebase -> refaz os commits da feature em cima da main: histórico linear

def demo_merge_vs_rebase():
    print("=== MERGE ===\n")
    pasta = _pasta_de_treino('git-treino-merge')
    _historia_divergente(pasta)
    _git(pasta, 'merge', 'feature', '--no-edit')
    print(_grafico(pasta))
    print("<- o commit de merge junta as duas linhas; o histórico mostra o paralelismo\n")

    print("=== REBASE ===\n")
    pasta = _pasta_de_treino('git-treino-rebase')
    _historia_divergente(pasta)
    hash_antes = _git(pasta, 'rev-parse', '--short', 'feature').stdout.strip()

    _git(pasta, 'checkout', 'feature')
    _git(pasta, 'rebase', 'main')
    hash_depois = _git(pasta, 'rev-parse', '--short', 'feature').stdout.strip()

    _git(pasta, 'checkout', 'main')
    _git(pasta, 'merge', 'feature')  # agora é fast-forward: main só "anda" até a feature
    print(_grafico(pasta))
    print("<- linha reta, sem commit de merge\n")

    print(f"Último commit da feature: {hash_antes} (antes) -> {hash_depois} (depois)")
    print("O conteúdo é o mesmo, mas o rebase REESCREVE os commits (hashes novos).")
    print("Por isso nunca se faz rebase de branch que outras pessoas já baixaram.")


# --- conflito ---------------------------------------------------------------
# Conflito acontece quando as duas branches alteram a MESMA linha. O git
# não decide por você: para no meio, marca o arquivo e espera.
#
# Esta demo monta o conflito e PARA de propósito, deixando o repositório
# na pasta temporária pra você resolver na mão, no VS Code.

def demo_criar_conflito():
    pasta = _pasta_de_treino('git-treino-conflito')
    _commit(pasta, 'config.txt', 'timeout=30\nretries=3\n', 'commit inicial')

    _git(pasta, 'checkout', '-b', 'feature')
    _commit(pasta, 'config.txt', 'timeout=60\nretries=3\n', 'feature: timeout para 60')

    _git(pasta, 'checkout', 'main')
    _commit(pasta, 'config.txt', 'timeout=45\nretries=3\n', 'main: timeout para 45')

    resultado = _git(pasta, 'merge', 'feature')
    print(f"Código de saída do merge: {resultado.returncode}  (diferente de 0 = conflito)\n")

    print("git status --short:")
    print(_git(pasta, 'status', '--short').stdout)
    print("(UU = arquivo alterado dos dois lados, ainda sem merge)\n")

    print("Conteúdo do config.txt agora:")
    print((pasta / 'config.txt').read_text(encoding='utf-8'))

    print(f"Repositório parado em conflito, esperando você:\n  {pasta}")