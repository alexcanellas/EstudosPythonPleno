"""
CLEAN CODE. Cada tópico tem o código RUIM ao lado do BOM.

Rode no shell:

    from boas_praticas.clean_code import *
    demo_nomes()
    demo_funcoes_pequenas()
    demo_guard_clauses()
    demo_numeros_magicos()
    demo_duplicacao()
    demo_argumento_mutavel()
"""

import inspect
from dataclasses import dataclass
from decimal import Decimal
from enum import IntEnum


# ===========================================================================
# 1. NOMES QUE REVELAM A INTENÇÃO
# ===========================================================================
# O nome deve responder: o que é isto, por que existe, como se usa. Se
# precisa de um comentário para explicar um nome, o nome está errado.

DADOS_CLIENTES = [('Ana', 150), ('Bruno', 40), ('Carla', 300)]


def calc(l, d):
    """RUIM: o que é l? o que é d? o que significa x[1]?"""
    r = []
    for x in l:
        if x[1] > d:
            r.append(x[0])
    return r


@dataclass(frozen=True)
class Cliente:
    nome: str
    divida: int


CLIENTES = [Cliente(nome, divida) for nome, divida in DADOS_CLIENTES]


def nomes_dos_devedores_acima_de(clientes, limite):
    """BOM: o nome da função, dos parâmetros e dos campos contam a história."""
    return [cliente.nome for cliente in clientes if cliente.divida > limite]


def demo_nomes():
    print('Chamada com nomes ruins (o que são l, d, x[1]?):')
    print(f'  calc(DADOS_CLIENTES, 100) -> {calc(DADOS_CLIENTES, 100)}')

    print('\nChamada com nomes que revelam a intenção:')
    resultado = nomes_dos_devedores_acima_de(CLIENTES, limite=100)
    print(f'  nomes_dos_devedores_acima_de(CLIENTES, limite=100) -> {resultado}')

    print('\nMesmo resultado. A diferença é o custo de LER, e quem vai ler é você')
    print('daqui a seis meses, sem lembrar de nada.')


# ===========================================================================
# 2. FUNÇÕES PEQUENAS, COM UM NÍVEL DE ABSTRAÇÃO
# ===========================================================================
# O critério não é um número de linhas. É: a função mistura "o quê" com
# "como"? A boa lê como um resumo, e os detalhes ficam em funções com nome.

PEDIDO_PEQUENO = {'itens': [
    {'nome': 'Caneta', 'preco': Decimal('3.50'), 'quantidade': 10},
    {'nome': 'Caderno', 'preco': Decimal('18.90'), 'quantidade': 3},
]}

PEDIDO_GRANDE = {'itens': [
    {'nome': 'Mochila', 'preco': Decimal('120.00'), 'quantidade': 5},
    {'nome': 'Caneta', 'preco': Decimal('3.50'), 'quantidade': 10},
]}


def processar_pedido_ruim(pedido):
    """RUIM: valida, calcula, aplica regra e formata, tudo misturado."""
    if not pedido.get('itens'):
        raise ValueError('Pedido sem itens')
    for item in pedido['itens']:
        if item['quantidade'] <= 0:
            raise ValueError(f"Quantidade inválida para {item['nome']}")

    subtotal = Decimal('0')
    linhas = []
    for item in pedido['itens']:
        parcial = item['preco'] * item['quantidade']
        subtotal += parcial
        linhas.append(
            f"{item['nome']}: {item['quantidade']} x {item['preco']:.2f} = {parcial:.2f}"
        )

    total = subtotal
    if subtotal >= 500:
        desconto = subtotal * Decimal('0.10')
        total = subtotal - desconto
        linhas.append(f'Desconto: -{desconto:.2f}')
    linhas.append(f'TOTAL: {total:.2f}')
    return '\n'.join(linhas)


LIMITE_PARA_DESCONTO = Decimal('500')
PERCENTUAL_DESCONTO = Decimal('0.10')


def validar_pedido(pedido):
    if not pedido.get('itens'):
        raise ValueError('Pedido sem itens')
    for item in pedido['itens']:
        if item['quantidade'] <= 0:
            raise ValueError(f"Quantidade inválida para {item['nome']}")


def subtotal_do_item(item):
    return item['preco'] * item['quantidade']


def calcular_subtotal(itens):
    return sum(subtotal_do_item(item) for item in itens)


def desconto_por_volume(subtotal):
    if subtotal < LIMITE_PARA_DESCONTO:
        return Decimal('0')
    return subtotal * PERCENTUAL_DESCONTO


def formatar_recibo(itens, desconto, total):
    linhas = [
        f"{item['nome']}: {item['quantidade']} x {item['preco']:.2f} "
        f'= {subtotal_do_item(item):.2f}'
        for item in itens
    ]
    if desconto:
        linhas.append(f'Desconto: -{desconto:.2f}')
    linhas.append(f'TOTAL: {total:.2f}')
    return '\n'.join(linhas)


def processar_pedido(pedido):
    """BOM: lê como um resumo. Cada passo tem nome e pode ser testado sozinho."""
    validar_pedido(pedido)
    itens = pedido['itens']
    subtotal = calcular_subtotal(itens)
    desconto = desconto_por_volume(subtotal)
    return formatar_recibo(itens, desconto, subtotal - desconto)


def demo_funcoes_pequenas():
    for titulo, pedido in (('pequeno', PEDIDO_PEQUENO), ('grande', PEDIDO_GRANDE)):
        ruim = processar_pedido_ruim(pedido)
        bom = processar_pedido(pedido)
        print(f'--- pedido {titulo} ---')
        print(bom)
        print(f'  (idêntico à versão de uma função só: {ruim == bom})\n')

    print('Cada peça agora é testável sozinha, sem montar um pedido inteiro:')
    print(f'  desconto_por_volume(499.99) = {desconto_por_volume(Decimal("499.99"))}')
    print(f'  desconto_por_volume(500)    = {desconto_por_volume(Decimal("500"))}')

    try:
        processar_pedido({'itens': []})
    except ValueError as erro:
        print(f'  pedido vazio -> ValueError: {erro}')


# ===========================================================================
# 3. GUARD CLAUSES: RETORNAR CEDO, SEM PIRÂMIDE DE IFS
# ===========================================================================
# Em vez de aninhar "se tudo estiver certo", trate cada caso de saída
# primeiro e deixe o caminho feliz no final, sem indentação extra.

DESCONTO_CLIENTE_FIEL = Decimal('0.15')
DESCONTO_CLIENTE_COMUM = Decimal('0.05')
SEM_DESCONTO = Decimal('0')
COMPRAS_PARA_SER_FIEL = 10


def desconto_do_cliente_ruim(cliente):
    """RUIM: a pirâmide de ifs, e o caminho feliz perdido lá no fundo."""
    if cliente is not None:
        if cliente['ativo']:
            if cliente['compras'] > 0:
                if cliente['compras'] >= 10:
                    return Decimal('0.15')
                else:
                    return Decimal('0.05')
            else:
                return Decimal('0')
        else:
            return Decimal('0')
    else:
        return Decimal('0')


def desconto_do_cliente(cliente):
    """BOM: cada caso de saída é tratado e descartado logo no começo."""
    if cliente is None:
        return SEM_DESCONTO
    if not cliente['ativo']:
        return SEM_DESCONTO
    if cliente['compras'] == 0:
        return SEM_DESCONTO
    if cliente['compras'] >= COMPRAS_PARA_SER_FIEL:
        return DESCONTO_CLIENTE_FIEL
    return DESCONTO_CLIENTE_COMUM


def _indentacao_maxima(funcao):
    """Mede o nível mais fundo de indentação do corpo de uma função."""
    linhas = inspect.getsource(funcao).splitlines()[1:]  # ignora a linha do def
    return max(
        (len(linha) - len(linha.lstrip())) // 4
        for linha in linhas
        if linha.strip() and not linha.strip().startswith('#')
    )


def demo_guard_clauses():
    casos = [
        ('sem cliente', None),
        ('inativo', {'ativo': False, 'compras': 20}),
        ('nunca comprou', {'ativo': True, 'compras': 0}),
        ('comum', {'ativo': True, 'compras': 3}),
        ('fiel', {'ativo': True, 'compras': 12}),
    ]

    print(f'{"caso":15} {"ruim":>6} {"bom":>6}')
    iguais = True
    for nome, cliente in casos:
        ruim = desconto_do_cliente_ruim(cliente)
        bom = desconto_do_cliente(cliente)
        iguais = iguais and ruim == bom
        print(f'{nome:15} {ruim!s:>6} {bom!s:>6}')

    print(f'\nMesmo comportamento nos 5 casos: {iguais}')
    print(f'Nível máximo de indentação: {_indentacao_maxima(desconto_do_cliente_ruim)} (ruim) '
          f'x {_indentacao_maxima(desconto_do_cliente)} (bom)')
    print('Na versão boa, cada if responde UMA pergunta, e o caminho feliz fica no fim.')


# ===========================================================================
# 4. NÚMEROS MÁGICOS: DÊ NOME AO QUE O NÚMERO SIGNIFICA
# ===========================================================================

def descrever_status_ruim(status):
    """RUIM: o que são 1, 2 e 3? Um 22 por engano cai no "desconhecido"."""
    if status == 1:
        return 'aguardando pagamento'
    elif status == 2:
        return 'pago'
    elif status == 3:
        return 'enviado'
    return 'desconhecido'


def pedido_expirado_ruim(segundos_desde_criacao):
    """RUIM: de onde vem 86400? Mudar o prazo exige caçar o literal."""
    return segundos_desde_criacao > 86400


class StatusPedido(IntEnum):
    AGUARDANDO_PAGAMENTO = 1
    PAGO = 2
    ENVIADO = 3


DESCRICAO_DO_STATUS = {
    StatusPedido.AGUARDANDO_PAGAMENTO: 'aguardando pagamento',
    StatusPedido.PAGO: 'pago',
    StatusPedido.ENVIADO: 'enviado',
}

SEGUNDOS_POR_DIA = 24 * 60 * 60
PRAZO_DE_EXPIRACAO_EM_SEGUNDOS = SEGUNDOS_POR_DIA


def descrever_status(status):
    # StatusPedido(status) VALIDA: um valor fora do enum levanta ValueError
    # na hora, em vez de seguir adiante em silêncio.
    return DESCRICAO_DO_STATUS[StatusPedido(status)]


def pedido_expirado(segundos_desde_criacao):
    return segundos_desde_criacao > PRAZO_DE_EXPIRACAO_EM_SEGUNDOS


def demo_numeros_magicos():
    print('SEM nome:')
    print(f'  descrever_status_ruim(2)  -> {descrever_status_ruim(2)}')
    print(f'  descrever_status_ruim(22) -> {descrever_status_ruim(22)}  <- erro de digitação passa em silêncio')
    print(f'  pedido_expirado_ruim(90000) -> {pedido_expirado_ruim(90000)}  (e o que é 86400?)\n')

    print('COM Enum e constantes:')
    print(f'  StatusPedido(2)         -> {StatusPedido(2)!r}')
    print(f'  StatusPedido.PAGO == 2  -> {StatusPedido.PAGO == 2}  (IntEnum ainda compara com int)')
    print(f'  descrever_status(StatusPedido.PAGO) -> {descrever_status(StatusPedido.PAGO)}')

    try:
        descrever_status(22)
    except ValueError as erro:
        print(f'  descrever_status(22)    -> ValueError: {erro}')

    try:
        StatusPedido.PAGOO
    except AttributeError as erro:
        print(f'  StatusPedido.PAGOO      -> {type(erro).__name__} (typo vira erro, não bug)')

    print(f'  pedido_expirado(90000)  -> {pedido_expirado(90000)}  '
          f'(prazo: {PRAZO_DE_EXPIRACAO_EM_SEGUNDOS} s = 1 dia, com nome)')


# ===========================================================================
# 5. DUPLICAÇÃO (DRY): UMA REGRA, UM LUGAR
# ===========================================================================
# DRY é sobre CONHECIMENTO, e não sobre texto parecido. A regra "a alíquota
# é 18%" não pode morar em dois lugares, senão um deles envelhece.

def total_do_carrinho_ruim(valores):
    return sum(valor * Decimal('1.18') for valor in valores)


def linha_da_nota_ruim(nome, valor):
    return f'{nome}: {valor * Decimal("1.18"):.2f}'  # a MESMA regra, copiada


ALIQUOTA_IMPOSTO = Decimal('0.18')


def preco_com_imposto(valor):
    return valor * (1 + ALIQUOTA_IMPOSTO)


def total_do_carrinho(valores):
    return sum(preco_com_imposto(valor) for valor in valores)


def linha_da_nota(nome, valor):
    return f'{nome}: {preco_com_imposto(valor):.2f}'


def demo_duplicacao():
    global ALIQUOTA_IMPOSTO
    valor = Decimal('100')

    print('SEM DRY, com a alíquota em 18%:')
    print(f'  carrinho: {total_do_carrinho_ruim([valor]):.2f}')
    print(f'  {linha_da_nota_ruim("nota", valor)}')

    print('\nA alíquota sobe para 20%, e alguém corrige só a nota:')
    nota_corrigida = valor * Decimal('1.20')
    carrinho_esquecido = total_do_carrinho_ruim([valor])
    print(f'  carrinho: {carrinho_esquecido:.2f}   nota: {nota_corrigida:.2f}'
          f'  <- o cliente vê dois preços')

    print('\nCOM DRY, mudando a constante UMA vez:')
    original = ALIQUOTA_IMPOSTO
    ALIQUOTA_IMPOSTO = Decimal('0.20')
    try:
        print(f'  carrinho: {total_do_carrinho([valor]):.2f}')
        print(f'  {linha_da_nota("nota", valor)}')
    finally:
        ALIQUOTA_IMPOSTO = original  # restaura, pra não sujar a sessão

    print('\nOs dois acompanharam a regra. Cuidado com o exagero: duas funções que')
    print('SE PARECEM mas mudam por motivos diferentes devem continuar separadas.')


# ===========================================================================
# 6. ARMADILHA DO PYTHON: ARGUMENTO PADRÃO MUTÁVEL
# ===========================================================================
# O valor padrão de um parâmetro é calculado UMA vez, quando o `def` é
# executado, e não a cada chamada. Com uma lista, todas as chamadas
# compartilham a MESMA lista. (A função também é um objeto, como vimos em
# decorators.)

def adicionar_item_ruim(item, carrinho=[]):
    carrinho.append(item)
    return carrinho


def adicionar_item(item, carrinho=None):
    # None é o "sentinela": a lista nova nasce DENTRO da função, a cada chamada.
    if carrinho is None:
        carrinho = []
    carrinho.append(item)
    return carrinho


def demo_argumento_mutavel():
    adicionar_item_ruim.__defaults__ = ([],)  # zera o estado, pra demo ser repetível

    print('SEM o None (default []):')
    primeira = list(adicionar_item_ruim('caneta'))
    segunda = adicionar_item_ruim('caderno')
    print(f'  1ª chamada: {primeira}')
    print(f'  2ª chamada: {segunda}')
    print("  Esperado na 2ª: ['caderno']. O [] do default foi reaproveitado.")
    print(f'  O default guardado na própria função: {adicionar_item_ruim.__defaults__}\n')

    print('COM o None:')
    print(f'  1ª chamada: {adicionar_item("caneta")}')
    print(f'  2ª chamada: {adicionar_item("caderno")}')
    print('  Cada chamada tem a sua lista.')