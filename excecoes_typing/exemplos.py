"""
EXCEÇÕES E TYPE HINTS — exemplos comentados.

Foco: hierarquia de exceções, exceções customizadas, try/except/else/finally
completo, raise...from (encadeamento), e os tipos mais usados do módulo
typing. Rode no shell:

    from excecoes_typing.exemplos import *
    demo_hierarquia_excecoes()
    demo_excecao_customizada()
    demo_try_except_else_finally()
    demo_raise_from()
    demo_type_hints_basicos()
"""

from typing import Optional, Union, List, Dict, Generic, TypeVar


# ---------------------------------------------------------------------------
# 1. HIERARQUIA DE EXCEÇÕES
# ---------------------------------------------------------------------------
# Toda exceção embutida do Python herda de BaseException, mas na prática
# você quase sempre lida com a árvore abaixo de Exception (BaseException
# cobre coisas como SystemExit e KeyboardInterrupt, que você geralmente
# NÃO quer capturar sem querer).
#
#   BaseException
#     └── Exception
#           ├── ValueError
#           ├── TypeError
#           ├── KeyError        (herda de LookupError)
#           ├── IndexError      (herda de LookupError)
#           ├── ZeroDivisionError (herda de ArithmeticError)
#           └── ...
#
# Isso importa na prática: como KeyError e IndexError são ambas
# LookupError, dá pra capturar as duas com um `except LookupError`.

def demo_hierarquia_excecoes():
    print("MRO de KeyError:")
    for classe in KeyError.__mro__:
        print(f"  -> {classe.__name__}")

    print("\nCapturando por uma classe mais genérica (LookupError):")
    try:
        d = {}
        d["chave_inexistente"]
    except LookupError as e:
        # pega tanto KeyError quanto IndexError, porque ambas são LookupError
        print(f"  Capturado como LookupError: {type(e).__name__}: {e}")

    print("\nOrdem dos except importa — do mais específico pro mais genérico:")
    try:
        d = {}
        d["chave_inexistente"]
    except KeyError:
        print("  Capturado como KeyError (mais específico, bate primeiro)")
    except LookupError:
        print("  Isso aqui nunca roda, porque KeyError já capturou antes")


# ---------------------------------------------------------------------------
# 2. EXCEÇÕES CUSTOMIZADAS
# ---------------------------------------------------------------------------
# Criar suas próprias exceções (herdando de Exception) deixa o código mais
# expressivo e permite carregar dados extras junto com o erro — muito
# usado em APIs (ex: DRF usa isso pra mapear erros pra status HTTP certos).

class SaldoInsuficienteError(Exception):
    """Levantada quando uma conta não tem saldo suficiente pra uma operação."""

    def __init__(self, saldo_atual, valor_solicitado):
        self.saldo_atual = saldo_atual
        self.valor_solicitado = valor_solicitado
        # monta uma mensagem legível, mas os dados brutos continuam
        # acessíveis via e.saldo_atual / e.valor_solicitado
        super().__init__(
            f"Saldo insuficiente: tem {saldo_atual}, precisa de {valor_solicitado}"
        )


def sacar(saldo, valor):
    if valor > saldo:
        raise SaldoInsuficienteError(saldo, valor)
    return saldo - valor


def demo_excecao_customizada():
    try:
        sacar(saldo=100, valor=500)
    except SaldoInsuficienteError as e:
        print(f"Erro: {e}")
        # a vantagem de exceção customizada: os dados ficam acessíveis
        # separadamente da mensagem, pra você usar em lógica (ex: numa
        # API, montar um JSON de erro estruturado)
        print(f"  Saldo atual: {e.saldo_atual}")
        print(f"  Valor solicitado: {e.valor_solicitado}")
        print(f"  Faltam: {e.valor_solicitado - e.saldo_atual}")


# ---------------------------------------------------------------------------
# 3. try / except / else / finally — o bloco completo
# ---------------------------------------------------------------------------
#   try:     código que pode falhar
#   except:  roda SE deu exceção (e ela bate no tipo capturado)
#   else:    roda SE NÃO deu exceção nenhuma (opcional, pouca gente usa)
#   finally: roda SEMPRE, deu erro ou não (limpeza de recursos)

def dividir(a, b):
    try:
        resultado = a / b
    except ZeroDivisionError:
        print("  [except] Não dá pra dividir por zero")
        return None
    else:
        # só roda se NÃO houve exceção — útil pra separar "o que pode
        # falhar" de "o que fazer quando deu certo"
        print(f"  [else] Divisão deu certo: {resultado}")
        return resultado
    finally:
        # roda sempre, independente de ter dado erro ou não
        print("  [finally] Operação de divisão finalizada")


def demo_try_except_else_finally():
    print("Caso 1: divisão válida")
    dividir(10, 2)

    print("\nCaso 2: divisão por zero")
    dividir(10, 0)


# ---------------------------------------------------------------------------
# 4. raise ... from ... — encadeamento de exceções
# ---------------------------------------------------------------------------
# Quando você captura uma exceção e levanta OUTRA no lugar dela, o `from`
# preserva a exceção original como "causa", em vez de esconder ela. Isso
# aparece no traceback como "The above exception was the direct cause of
# the following exception" — extremamente útil pra debugar em produção,
# porque sem isso você perde o contexto do erro original.

def buscar_usuario(usuario_id, banco_de_dados):
    try:
        return banco_de_dados[usuario_id]
    except KeyError as erro_original:
        # sem "from erro_original", a ValueError apareceria "do nada",
        # escondendo que a causa raiz foi um KeyError
        raise ValueError(f"Usuário {usuario_id} não encontrado") from erro_original


def demo_raise_from():
    banco_falso = {1: "Alexandre", 2: "Maria"}
    try:
        buscar_usuario(999, banco_falso)
    except ValueError as e:
        print(f"Exceção capturada: {e}")
        print(f"Causa original (via __cause__): {e.__cause__!r}")
        # e.__cause__ é o KeyError original — é isso que o "from" preserva


# ---------------------------------------------------------------------------
# 5. TYPE HINTS — Optional, Union, List, Dict, Generic
# ---------------------------------------------------------------------------
# Type hints não mudam o comportamento em tempo de execução (Python
# continua duck-typed), mas ajudam ferramentas (mypy, IDEs, DRF, FastAPI)
# a pegar erros ANTES de rodar, e documentam a intenção do código.

def buscar_nome(usuario_id: int) -> Optional[str]:
    """Optional[str] = Union[str, None] -> pode devolver string OU None."""
    banco = {1: "Alexandre", 2: "Maria"}
    return banco.get(usuario_id)  # .get() devolve None se não achar


def processar_id(valor: Union[int, str]) -> str:
    """Union[int, str] = aceita int OU str como entrada."""
    return str(valor).zfill(5)  # preenche com zeros à esquerda até 5 dígitos


def somar_lista(numeros: List[int]) -> int:
    """List[int] = lista onde TODO elemento deve ser int."""
    return sum(numeros)


def contar_palavras(texto: str) -> Dict[str, int]:
    """Dict[str, int] = dicionário com chaves str e valores int."""
    palavras = texto.split()
    contagem: Dict[str, int] = {}
    for palavra in palavras:
        contagem[palavra] = contagem.get(palavra, 0) + 1
    return contagem


# Generic: criar uma classe que funciona com qualquer tipo, mas mantendo
# a informação de tipo (diferente de usar `object` ou `Any`, que perdem
# a informação). Muito comum em estruturas tipo "Caixa que guarda um X".
T = TypeVar("T")


class Caixa(Generic[T]):
    def __init__(self, conteudo: T):
        self.conteudo = conteudo

    def abrir(self) -> T:
        return self.conteudo


def demo_type_hints_basicos():
    print("Optional[str]:")
    print(" ", buscar_nome(1))    # 'Alexandre'
    print(" ", buscar_nome(999))  # None

    print("\nUnion[int, str]:")
    print(" ", processar_id(42))
    print(" ", processar_id("7"))

    print("\nList[int]:")
    print(" ", somar_lista([1, 2, 3, 4]))

    print("\nDict[str, int]:")
    print(" ", contar_palavras("python é bom python é produtivo"))

    print("\nGeneric[T]:")
    caixa_int = Caixa(42)          # Caixa[int]
    caixa_str = Caixa("Alexandre")  # Caixa[str]
    print(f"  Caixa com int: {caixa_int.abrir()}")
    print(f"  Caixa com str: {caixa_str.abrir()}")
    # numa IDE com suporte a type checking, caixa_int.abrir() é sabido
    # como int, e caixa_str.abrir() como str — sem precisar de cast manual