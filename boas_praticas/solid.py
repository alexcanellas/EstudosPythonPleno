"""
SOLID. Cada princípio tem o código RUIM ao lado do BOM.

Rode no shell:

    from boas_praticas.solid import *
    demo_srp()
    demo_dip()
    demo_ocp()
    demo_lsp()
    demo_isp()
"""

from decimal import Decimal
from typing import Protocol

from abc import ABC, abstractmethod
from dataclasses import dataclass




# ===========================================================================
# S: SINGLE RESPONSIBILITY PRINCIPLE
# "Uma classe deve ter um único motivo para mudar."
# ===========================================================================
# O erro comum é ler "uma responsabilidade" como "faz uma coisa só". A
# pergunta útil é: QUEM pediria uma mudança aqui? Se o financeiro, o time
# de design e o time de infra mexem na mesma classe, ela tem três motivos
# para mudar, e uma alteração de um pode quebrar o que os outros usam.

VENDAS = [
    {'produto': 'Caneta', 'valor': Decimal('3.50'), 'quantidade': 10},
    {'produto': 'Caderno', 'valor': Decimal('18.90'), 'quantidade': 3},
    {'produto': 'Mochila', 'valor': Decimal('120.00'), 'quantidade': 1},
]


class RelatorioDeVendasRuim:
    """VIOLA o SRP: três motivos para mudar na mesma classe."""

    def __init__(self, vendas):
        self.vendas = vendas

    def total(self):
        # Motivo 1, REGRA DE NEGÓCIO: o financeiro pede para somar imposto.
        return sum(v['valor'] * v['quantidade'] for v in self.vendas)

    def como_texto(self):
        # Motivo 2, APRESENTAÇÃO: pedem o relatório em CSV.
        linhas = [
            f"{v['produto']}: {v['quantidade']} x {v['valor']:.2f}"
            for v in self.vendas
        ]
        linhas.append(f"TOTAL: {self.total():.2f}")
        return '\n'.join(linhas)

    def salvar(self, caminho):
        # Motivo 3, INFRAESTRUTURA: trocam o arquivo local por um bucket S3.
        # (A demo não chama este método, pra não gravar nada no seu disco.)
        with open(caminho, 'w', encoding='utf-8') as arquivo:
            arquivo.write(self.como_texto())


# --- Versão corrigida: cada peça tem UM motivo para mudar -------------------
# Funções simples bastam. Em Python, não é obrigatório transformar tudo em
# classe só para "parecer orientado a objetos".

def calcular_total(vendas):
    """Só regra de negócio. Não sabe que existe texto, CSV ou arquivo."""
    return sum(v['valor'] * v['quantidade'] for v in vendas)


def formatar_como_texto(vendas, total):
    """Só apresentação."""
    linhas = [
        f"{v['produto']}: {v['quantidade']} x {v['valor']:.2f} "
        f"= {v['valor'] * v['quantidade']:.2f}"
        for v in vendas
    ]
    linhas.append(f"TOTAL: {total:.2f}")
    return '\n'.join(linhas)


def formatar_como_csv(vendas, total):
    """Formato novo: nasceu SEM encostar em nenhuma linha do cálculo."""
    linhas = ['produto,quantidade,valor_unitario']
    linhas += [f"{v['produto']},{v['quantidade']},{v['valor']:.2f}" for v in vendas]
    linhas.append(f"total,,{total:.2f}")
    return '\n'.join(linhas)


def gravar(conteudo, caminho):
    """Só infraestrutura. Trocar por S3 mexe apenas aqui."""
    with open(caminho, 'w', encoding='utf-8') as arquivo:
        arquivo.write(conteudo)


def demo_srp():
    total = calcular_total(VENDAS)
    print(f"Total (só a regra de negócio, sem formatar nada): {total:.2f}\n")

    print("--- texto ---")
    print(formatar_como_texto(VENDAS, total))

    print("\n--- csv (formato novo) ---")
    print(formatar_como_csv(VENDAS, total))

    print("\nAdicionar o CSV não tocou no cálculo. Mudar o imposto não toca no")
    print("formato. Trocar o destino não toca em nenhum dos dois.")
    print("Teste: calcular_total roda sozinha, sem precisar de texto nem de disco.")


# ===========================================================================
# D: DEPENDENCY INVERSION PRINCIPLE
# "Módulos de alto nível não devem depender de detalhes concretos.
#  Ambos devem depender de abstrações."
# ===========================================================================
# Em termos práticos: uma classe que precisa de e-mail, banco ou API não
# deve CRIAR essa dependência por dentro. Ela a RECEBE de fora. Foi o que
# o LivroService fez na Categoria 6 ao receber os repositórios no
# construtor, e é a mesma ideia do Depends() do FastAPI.

class ServidorEmail:
    """Um detalhe concreto. Explode de propósito (mesma ideia do servicos.py
    da Categoria 4) para provar que ele foi acionado de verdade."""

    def enviar(self, destinatario, mensagem):
        raise RuntimeError('Enviou e-mail REAL! Em teste isso não deveria acontecer.')


class NotificadorRuim:
    """VIOLA o DIP: cria o próprio ServidorEmail por dentro."""

    def __init__(self):
        self.canal = ServidorEmail()  # acoplamento direto a um detalhe concreto

    def avisar_pedido_pronto(self, cliente, numero_pedido):
        self.canal.enviar(cliente, f'Seu pedido #{numero_pedido} está pronto.')


# --- Versão corrigida --------------------------------------------------------
# Protocol descreve a FORMA que a dependência precisa ter. Quem tiver um
# método enviar(destinatario, mensagem) serve, SEM precisar herdar de nada
# (é o duck typing com type hint que vimos em excecoes_typing). A checagem
# é feita por ferramentas como mypy e pela IDE, não em tempo de execução.

class CanalDeNotificacao(Protocol):
    def enviar(self, destinatario: str, mensagem: str) -> None: ...


class NotificadorDePedido:
    """A regra de negócio não sabe se a mensagem vai por e-mail, SMS ou log."""

    def __init__(self, canal: CanalDeNotificacao):
        self.canal = canal  # recebido de fora: injeção de dependência

    def avisar_pedido_pronto(self, cliente: str, numero_pedido: int) -> None:
        self.canal.enviar(cliente, f'Seu pedido #{numero_pedido} está pronto.')


class CanalFalso:
    """Para testes: não envia nada, só guarda o que receberia."""

    def __init__(self):
        self.enviadas = []

    def enviar(self, destinatario, mensagem):
        self.enviadas.append((destinatario, mensagem))


class CanalConsole:
    """Outro canal, para provar que o Notificador é intercambiável."""

    def enviar(self, destinatario, mensagem):
        print(f'  [console] para {destinatario}: {mensagem}')


def demo_dip():
    print('SEM inversão: o notificador cria o próprio ServidorEmail')
    try:
        NotificadorRuim().avisar_pedido_pronto('ana@email.com', 42)
    except RuntimeError as erro:
        print(f'  Quebrou: {erro}')
    print('  Para testar a regra, foi preciso disparar o envio real.\n')

    print('COM inversão: o canal chega de fora')
    falso = CanalFalso()
    NotificadorDePedido(falso).avisar_pedido_pronto('ana@email.com', 42)
    print(f'  Mensagens capturadas, sem enviar nada: {falso.enviadas}')

    print('\nMesmo notificador, outro canal (nenhuma linha dele mudou):')
    NotificadorDePedido(CanalConsole()).avisar_pedido_pronto('bruno@email.com', 43)


# ===========================================================================
# O: OPEN/CLOSED PRINCIPLE
# "Aberto para extensão, fechado para modificação."
# ===========================================================================
# Novo comportamento deve entrar SEM editar o código que já funciona. Cada
# edição numa função testada é uma chance de quebrar o que estava certo.

def calcular_frete_ruim(tipo, peso):
    """VIOLA o OCP: todo tipo de frete novo exige EDITAR esta função."""
    if tipo == 'correios':
        return Decimal('10') + Decimal('2') * peso
    elif tipo == 'transportadora':
        return Decimal('25') + Decimal('1') * peso
    elif tipo == 'retirada':
        return Decimal('0')
    raise ValueError(f'Tipo de frete desconhecido: {tipo}')


# --- Versão corrigida: um registro de regras -------------------------------
# Cada regra de frete é um objeto com o método calcular(peso). O decorator
# (o mesmo mecanismo da Categoria 1) registra a regra num dicionário. Quem
# calcula o frete só consulta o dicionário e nunca precisa ser editado.

FRETES = {}


def frete(nome):
    def decorator(classe):
        FRETES[nome] = classe()
        return classe
    return decorator


@frete('correios')
class Correios:
    def calcular(self, peso):
        return Decimal('10') + Decimal('2') * peso


@frete('transportadora')
class Transportadora:
    def calcular(self, peso):
        return Decimal('25') + Decimal('1') * peso


@frete('retirada')
class Retirada:
    def calcular(self, peso):
        return Decimal('0')


def calcular_frete(tipo, peso):
    """FECHADA para modificação: esta função não muda quando surge um tipo novo."""
    try:
        regra = FRETES[tipo]
    except KeyError:
        raise ValueError(f'Tipo de frete desconhecido: {tipo}') from None
    return regra.calcular(peso)


def demo_ocp():
    peso = Decimal('3')

    print('SEM OCP (if/elif):')
    for tipo in ('correios', 'transportadora', 'retirada'):
        print(f'  {tipo:15} {calcular_frete_ruim(tipo, peso):.2f}')
    try:
        calcular_frete_ruim('motoboy', peso)
    except ValueError as erro:
        print(f'  motoboy         {erro}')
    print('  Para suportar o motoboy é preciso EDITAR a função, arriscando os outros três.\n')

    print('COM OCP (registro):')
    for tipo in sorted(FRETES):
        print(f'  {tipo:15} {calcular_frete(tipo, peso):.2f}')

    # Extensão feita agora, em tempo de execução, sem tocar em calcular_frete.
    @frete('motoboy')
    class Motoboy:
        def calcular(self, peso):
            return Decimal('15') + Decimal('1.5') * peso

    try:
        print(f'  {"motoboy (novo)":15} {calcular_frete("motoboy", peso):.2f}')
    finally:
        del FRETES['motoboy']  # limpa, pra não sujar o resto da sessão

    print('\nO tipo novo entrou criando uma classe. Nenhuma linha de calcular_frete mudou.')


# ===========================================================================
# L: LISKOV SUBSTITUTION PRINCIPLE
# "Onde se espera o tipo base, qualquer subtipo deve funcionar sem
#  surpresas."
# ===========================================================================
# O exemplo clássico: "um quadrado é um retângulo" na geometria, mas como
# classes mutáveis a herança QUEBRA o contrato.

class Retangulo:
    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura

    def area(self):
        return self.largura * self.altura


class QuadradoRuim(Retangulo):
    """VIOLA o LSP: para continuar quadrado, largura e altura andam juntas,
    e isso muda o comportamento que quem usa um Retangulo espera."""

    def __init__(self, lado):
        super().__init__(lado, lado)

    @property
    def largura(self):
        return self._lado

    @largura.setter
    def largura(self, valor):
        self._lado = valor

    @property
    def altura(self):
        return self._lado

    @altura.setter
    def altura(self, valor):
        self._lado = valor


def esticar_para_5x4(forma):
    """Código cliente. Escrito pensando em Retangulo: define largura e altura
    de forma independente e espera a área 20."""
    forma.largura = 5
    forma.altura = 4
    return forma.area()


# --- Versão corrigida: sem herança, com uma abstração comum ----------------
# Os dois são formas com area(), e só isso. Imutáveis (frozen=True), então
# nenhum setter pode quebrar a expectativa de ninguém.

class Forma(Protocol):
    def area(self) -> int: ...


@dataclass(frozen=True)
class RetanguloOk:
    largura: int
    altura: int

    def area(self) -> int:
        return self.largura * self.altura


@dataclass(frozen=True)
class QuadradoOk:
    lado: int

    def area(self) -> int:
        return self.lado * self.lado


def somar_areas(formas):
    """Funciona com QUALQUER forma, sem saber qual é qual."""
    return sum(forma.area() for forma in formas)


def demo_lsp():
    print('Código cliente: define 5x4 e espera área 20')
    print(f'  Retangulo:    {esticar_para_5x4(Retangulo(1, 1))}  (esperado: 20)')
    print(f'  QuadradoRuim: {esticar_para_5x4(QuadradoRuim(1))}  (esperado: 20)  <- quebrou')
    print('  O quadrado não é substituível: o mesmo código dá resultado diferente.\n')

    print('Versão corrigida: sem herança, via abstração Forma')
    formas = [RetanguloOk(5, 4), QuadradoOk(3)]
    for forma in formas:
        print(f'  {type(forma).__name__}: área {forma.area()}')
    print(f'  somar_areas: {somar_areas(formas)}  (qualquer forma entra, sem surpresa)')


# ===========================================================================
# I: INTERFACE SEGREGATION PRINCIPLE
# "Ninguém deve ser forçado a depender de métodos que não usa."
# ===========================================================================
# Interface gorda obriga as implementações a fingir que sabem fazer o que
# não sabem. O sintoma clássico é um método que só levanta
# NotImplementedError.

class MaquinaRuim(ABC):
    """VIOLA o ISP: junta três capacidades numa interface só."""

    @abstractmethod
    def imprimir(self, documento): ...

    @abstractmethod
    def escanear(self): ...

    @abstractmethod
    def enviar_fax(self, documento): ...


class ImpressoraSimplesRuim(MaquinaRuim):
    def imprimir(self, documento):
        return f'imprimindo {documento}'

    def escanear(self):
        raise NotImplementedError('Esta impressora não escaneia')

    def enviar_fax(self, documento):
        raise NotImplementedError('Esta impressora não envia fax')


# --- Versão corrigida: interfaces pequenas, uma por capacidade -------------

class Impressora(Protocol):
    def imprimir(self, documento: str) -> str: ...


class Scanner(Protocol):
    def escanear(self) -> str: ...


class ImpressoraSimples:
    def imprimir(self, documento):
        return f'imprimindo {documento}'


class Multifuncional:
    def imprimir(self, documento):
        return f'imprimindo {documento}'

    def escanear(self):
        return 'imagem digitalizada'


def imprimir_documento(impressora: Impressora, documento):
    """Depende só de imprimir(). Aceita qualquer coisa que imprima."""
    return impressora.imprimir(documento)


def digitalizar_documento(scanner: Scanner):
    """Depende só de escanear()."""
    return scanner.escanear()


def demo_isp():
    print('SEM segregação (interface gorda):')
    gorda = ImpressoraSimplesRuim()
    print(f'  imprimir: {gorda.imprimir("contrato.pdf")}')
    for acao in (gorda.escanear, lambda: gorda.enviar_fax('contrato.pdf')):
        try:
            acao()
        except NotImplementedError as erro:
            print(f'  método "de mentira": {erro}')
    print('  Quem recebe uma MaquinaRuim não sabe quais métodos funcionam.\n')

    print('COM segregação (interfaces pequenas):')
    simples = ImpressoraSimples()
    multi = Multifuncional()
    print(f'  {imprimir_documento(simples, "contrato.pdf")}')
    print(f'  {imprimir_documento(multi, "contrato.pdf")}')
    print(f'  {digitalizar_documento(multi)}')

    try:
        digitalizar_documento(simples)  # type: ignore[arg-type]
    except AttributeError as erro:
        print(f'  Pedir scanner a uma impressora simples: {erro}')
    print('  O mypy e a IDE apontam esse erro ANTES de rodar, porque a função')
    print('  declara que precisa de um Scanner.')