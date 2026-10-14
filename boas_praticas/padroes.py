"""
DESIGN PATTERNS: Factory, Singleton e Strategy, na versão enxuta do Python.

Rode no shell:

    from boas_praticas.padroes import *
    demo_factory()
    demo_singleton()
    demo_strategy()
"""

import sys
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from typing import Callable


# ===========================================================================
# 1. FACTORY: um único lugar que sabe QUAL objeto criar
# ===========================================================================
# Quem usa o objeto não deveria precisar saber qual classe concreta
# instanciar. Sem factory, essa decisão se espalha pelo código, e um tipo
# novo exige lembrar de todos os lugares.

class PagamentoPix:
    def pagar(self, valor):
        return f'Pix de {valor:.2f} confirmado na hora'

    def estornar(self, valor):
        return f'Pix de {valor:.2f} devolvido'


class PagamentoCartao:
    def __init__(self, parcelas=1):
        self.parcelas = parcelas

    def pagar(self, valor):
        return f'Cartão em {self.parcelas}x de {valor / self.parcelas:.2f}'

    def estornar(self, valor):
        return f'Estorno de {valor:.2f} lançado na fatura'


class PagamentoBoleto:
    def pagar(self, valor):
        return f'Boleto de {valor:.2f} gerado (compensa em 3 dias úteis)'

    def estornar(self, valor):
        return f'Devolução de {valor:.2f} por transferência'


def checkout_ruim(tipo, valor):
    """RUIM: a decisão de qual classe criar mora aqui..."""
    if tipo == 'pix':
        pagamento = PagamentoPix()
    elif tipo == 'cartao':
        pagamento = PagamentoCartao(parcelas=3)
    elif tipo == 'boleto':
        pagamento = PagamentoBoleto()
    else:
        raise ValueError(f'Forma de pagamento desconhecida: {tipo!r}')
    return pagamento.pagar(valor)


def estornar_ruim(tipo, valor):
    """...e aqui, copiada. Um tipo novo precisa ser lembrado nos DOIS lugares."""
    if tipo == 'pix':
        pagamento = PagamentoPix()
    elif tipo == 'cartao':
        pagamento = PagamentoCartao(parcelas=3)
    elif tipo == 'boleto':
        pagamento = PagamentoBoleto()
    else:
        raise ValueError(f'Forma de pagamento desconhecida: {tipo!r}')
    return pagamento.estornar(valor)


# --- Versão corrigida: a factory é um dicionário de classes -----------------
# Em Python a classe é um objeto, então ela pode ser guardada num dict e
# chamada depois. Não precisa de hierarquia de "FactoryDePagamento".

FORMAS_DE_PAGAMENTO = {
    'pix': PagamentoPix,
    'cartao': PagamentoCartao,
    'boleto': PagamentoBoleto,
}


def criar_pagamento(tipo, **opcoes):
    try:
        construtor = FORMAS_DE_PAGAMENTO[tipo]
    except KeyError:
        raise ValueError(f'Forma de pagamento desconhecida: {tipo!r}') from None
    return construtor(**opcoes)


def checkout(tipo, valor, **opcoes):
    return criar_pagamento(tipo, **opcoes).pagar(valor)


def estornar(tipo, valor, **opcoes):
    return criar_pagamento(tipo, **opcoes).estornar(valor)


# --- A outra cara da factory em Python: o classmethod -----------------------
# É o "construtor alternativo" do Funcionario.da_string, lá no oop_avancado.

@dataclass(frozen=True)
class Dinheiro:
    centavos: int

    @classmethod
    def de_reais(cls, reais):
        # str() antes do Decimal: pelo mesmo motivo do float x Decimal da Categoria 3.
        centavos = (Decimal(str(reais)) * 100).to_integral_value()
        return cls(int(centavos))

    @classmethod
    def de_texto(cls, texto):
        # 'R$ 1.234,50' -> '1234.50'
        limpo = texto.replace('R$', '').strip().replace('.', '').replace(',', '.')
        return cls.de_reais(limpo)

    def __str__(self):
        return f'R$ {self.centavos / 100:.2f}'


def demo_factory():
    valor = Decimal('100')

    print('SEM factory (a cadeia de ifs repetida em dois lugares):')
    print(f'  {checkout_ruim("cartao", valor)}')
    print(f'  {estornar_ruim("cartao", valor)}\n')

    print('COM factory (a decisão mora num lugar só):')
    for tipo, opcoes in (('pix', {}), ('cartao', {'parcelas': 3}), ('boleto', {})):
        print(f'  {checkout(tipo, valor, **opcoes)}')
    print(f'  {estornar("pix", valor)}')

    try:
        checkout('cripto', valor)
    except ValueError as erro:
        print(f'  tipo inexistente -> ValueError: {erro}')

    print('\nclassmethod como factory (construtores alternativos):')
    print(f'  Dinheiro.de_reais("19.90")      -> {Dinheiro.de_reais("19.90")} '
          f'(centavos={Dinheiro.de_reais("19.90").centavos})')
    print(f'  Dinheiro.de_texto("R$ 1.234,50") -> {Dinheiro.de_texto("R$ 1.234,50")}')

    print('\nUm pagamento novo entra como uma classe e uma linha no dicionário.')
    print('As funções checkout e estornar não mudam.')


# ===========================================================================
# 2. SINGLETON: uma única instância para o processo inteiro
# ===========================================================================
# É o padrão mais criticado, porque é estado global com cara de objeto. Ele
# aparece em entrevista tanto pra ser implementado quanto pra ser
# questionado. Em Python quase sempre existe uma forma mais simples.

class ConfigRuim:
    """RUIM: a armadilha clássica. O __new__ devolve a mesma instância, mas o
    __init__ roda A CADA chamada de ConfigRuim() e apaga o que foi guardado."""

    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia

    def __init__(self):
        self.valores = {}  # roda de novo a cada ConfigRuim()


class Configuracao:
    """BOM: o estado nasce DENTRO do __new__, uma única vez.

    Limitação: não é thread-safe. Duas threads chamando Configuracao() ao
    mesmo tempo, na primeira vez, poderiam criar duas instâncias. Em um caso
    real, a criação ficaria protegida por um threading.Lock."""

    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            instancia = super().__new__(cls)
            instancia.valores = {}
            cls._instancia = instancia
        return cls._instancia


# --- Singleton leve: lru_cache numa função ---------------------------------
# A função roda uma vez e o resultado fica guardado. Tem um botão de reset
# (cache_clear), que é o que falta no singleton clássico e atrapalha os testes.

@lru_cache(maxsize=None)
def obter_conexao():
    print('  [criando a conexão, isso só aparece quando ela é de fato criada]')
    return object()


def demo_singleton():
    ConfigRuim._instancia = None
    Configuracao._instancia = None
    obter_conexao.cache_clear()

    print('Singleton com __init__ (a armadilha):')
    a = ConfigRuim()
    a.valores['ambiente'] = 'producao'
    b = ConfigRuim()
    print(f'  a is b: {a is b}')
    print(f'  valores após o 2º ConfigRuim(): {b.valores}  <- o __init__ apagou tudo\n')

    print('Singleton correto (estado criado dentro do __new__):')
    a = Configuracao()
    a.valores['ambiente'] = 'producao'
    b = Configuracao()
    print(f'  a is b: {a is b}')
    print(f'  valores: {b.valores}\n')

    print('O módulo já é um singleton (o Python guarda em sys.modules):')
    import boas_praticas.padroes as via_import
    from boas_praticas import padroes as via_from
    print(f'  importado de dois jeitos, mesmo objeto: {via_import is via_from}')
    print(f'  registrado em sys.modules: {"boas_praticas.padroes" in sys.modules}')
    print('  É assim que o settings e o cache do Django funcionam: um objeto no')
    print('  nível do módulo, que todo mundo importa.\n')

    print('Singleton leve com lru_cache:')
    c1 = obter_conexao()
    c2 = obter_conexao()
    print(f'  c1 is c2: {c1 is c2}  (a mensagem de criação apareceu uma vez)')
    obter_conexao.cache_clear()
    c3 = obter_conexao()
    print(f'  após cache_clear, c3 is c1: {c3 is c1}  (reset possível, bom pra testes)\n')

    print('O custo: estado global vaza entre testes.')
    Configuracao().valores['modo'] = 'teste_1'
    print(f'  o "teste 2" já enxerga o que o "teste 1" gravou: {Configuracao().valores}')
    Configuracao._instancia = None
    print(f'  só depois de um reset manual fica limpo: {Configuracao().valores}')
    Configuracao._instancia = None  # deixa limpo pra próxima execução


# ===========================================================================
# 3. STRATEGY: trocar o algoritmo sem mudar quem o usa
# ===========================================================================
# A estratégia é injetada no objeto que a usa, e pode ser trocada em tempo
# de execução. Em Python, como função é objeto, a estratégia costuma ser
# só uma função. Não precisa de uma classe por algoritmo.
#
# Diferença para o registro do OCP (solid.py): lá a chave escolhe a regra
# DENTRO de uma função. Aqui a regra é entregue a quem a vai usar.

Estrategia = Callable[[Decimal], Decimal]  # recebe o subtotal, devolve o desconto


def sem_desconto(subtotal):
    return Decimal('0')


def desconto_percentual(percentual):
    """Fábrica de estratégias: devolve uma função já configurada."""
    def estrategia(subtotal):
        return subtotal * Decimal(str(percentual)) / 100
    return estrategia


def desconto_progressivo(subtotal):
    if subtotal >= 1000:
        return subtotal * Decimal('0.15')
    if subtotal >= 500:
        return subtotal * Decimal('0.10')
    return Decimal('0')


def total_ruim(itens, tipo_desconto):
    """RUIM: todo desconto novo exige editar este if/elif."""
    subtotal = sum(itens)
    if tipo_desconto == 'nenhum':
        desconto = Decimal('0')
    elif tipo_desconto == 'natal':
        desconto = subtotal * Decimal('0.10')
    elif tipo_desconto == 'progressivo':
        if subtotal >= 1000:
            desconto = subtotal * Decimal('0.15')
        elif subtotal >= 500:
            desconto = subtotal * Decimal('0.10')
        else:
            desconto = Decimal('0')
    else:
        raise ValueError(f'Desconto desconhecido: {tipo_desconto!r}')
    return subtotal - desconto


class Carrinho:
    """BOM: não sabe calcular desconto. Recebe quem sabe."""

    # O default é uma função, e função é imutável: não tem a armadilha do
    # argumento mutável que vimos no clean_code.
    def __init__(self, itens, estrategia_de_desconto: Estrategia = sem_desconto):
        self.itens = itens
        self.estrategia_de_desconto = estrategia_de_desconto

    def total(self):
        subtotal = sum(self.itens)
        return subtotal - self.estrategia_de_desconto(subtotal)


def demo_strategy():
    itens = [Decimal('300'), Decimal('450'), Decimal('250')]  # subtotal: 1000

    print('SEM strategy (o tipo vira texto e o if/elif decide):')
    for tipo in ('nenhum', 'natal', 'progressivo'):
        print(f'  {tipo:12} total = {total_ruim(itens, tipo):.2f}')

    print('\nCOM strategy (a regra é entregue ao carrinho):')
    estrategias = (
        ('nenhum', sem_desconto, 'nenhum'),
        ('natal 10%', desconto_percentual(10), 'natal'),
        ('progressivo', desconto_progressivo, 'progressivo'),
    )
    for nome, estrategia, tipo_antigo in estrategias:
        novo = Carrinho(itens, estrategia).total()
        antigo = total_ruim(itens, tipo_antigo)
        print(f'  {nome:12} total = {novo:.2f}  (igual à versão com if/elif: {novo == antigo})')

    print('\nTroca em tempo de execução, no mesmo carrinho:')
    carrinho = Carrinho(itens)
    print(f'  sem desconto:  {carrinho.total():.2f}')
    carrinho.estrategia_de_desconto = desconto_percentual(20)
    print(f'  depois de trocar para 20%: {carrinho.total():.2f}')

    print('\nStrategy está na biblioteca padrão, e você já usa sem notar:')
    produtos = [('Mochila', 120), ('Caneta', 4), ('Caderno', 19)]
    por_preco = [nome for nome, _ in sorted(produtos, key=lambda p: p[1])]
    por_nome = [nome for nome, _ in sorted(produtos, key=lambda p: p[0])]
    print(f'  sorted(key=preço): {por_preco}')
    print(f'  sorted(key=nome):  {por_nome}')
    print('  O algoritmo de ordenar é o mesmo. O critério é a estratégia.')
    