"""
OOP AVANÇADO — exemplos comentados.

Este arquivo é a parte "de verdade" do estudo. O HTML do app só te manda
pra cá. Rode cada função isolada no shell do Django (python manage.py shell)
pra ver o comportamento:

    from oop_avancado.exemplos import *
    demo_mro()
    demo_property()
    ...
"""


# ---------------------------------------------------------------------------
# 1. HERANÇA MÚLTIPLA E MRO (Method Resolution Order)
# ---------------------------------------------------------------------------
# Quando uma classe herda de mais de uma, o Python precisa decidir em que
# ordem procurar métodos/atributos. Essa ordem é o MRO, calculado pelo
# algoritmo C3 linearization. `super()` NÃO chama "a classe pai" — ele chama
# "o próximo na fila do MRO", o que é diferente em heranças múltiplas.

class Motor:
    def ligar(self):
        # Propaga o super() também, senão a cadeia para aqui e
        # SistemaEletrico.ligar() nunca seria chamado de verdade.
        anterior = super().ligar() if hasattr(super(), 'ligar') else ""
        proprio = "Motor ligado"
        return f"{anterior} + {proprio}".strip(' +') if anterior else proprio


class SistemaEletrico:
    def ligar(self):
        anterior = super().ligar() if hasattr(super(), 'ligar') else ""
        return f"{anterior} + Sistema elétrico ativado".strip(' +')


class Carro(Motor, SistemaEletrico):
    def ligar(self):
        # super() aqui segue o MRO de Carro: Carro -> Motor -> SistemaEletrico -> object
        return f"{super().ligar()} + Carro pronto pra rodar"


def demo_mro():
    print("MRO do Carro:")
    for classe in Carro.__mro__:
        print(f"  -> {classe.__name__}")

    carro = Carro()
    print(carro.ligar())
    # Repare: Carro só chama super().ligar() UMA vez, mas o MRO encadeia
    # a chamada por TODAS as classes na linha — isso é o "cooperative
    # multiple inheritance". Saída: Sistema elétrico ativado + Motor
    # ligado + Carro pronto pra rodar


# ---------------------------------------------------------------------------
# 2. CLASSMETHOD vs STATICMETHOD vs INSTANCE METHOD
# ---------------------------------------------------------------------------
class Funcionario:
    empresa = "CRCRJ"  # atributo de classe, compartilhado por todas as instâncias

    def __init__(self, nome, salario):
        self.nome = nome
        self.salario = salario

    def descricao(self):
        # instance method: recebe `self`, acessa dados da INSTÂNCIA
        return f"{self.nome} ganha {self.salario} na {self.empresa}"

    @classmethod
    def da_string(cls, texto_csv):
        # classmethod: recebe `cls` (a classe, não a instância).
        # Muito usado como "construtor alternativo".
        nome, salario = texto_csv.split(',')
        # cls(...) == Funcionario(...)
        return cls(nome.strip(), float(salario))

    @staticmethod
    def salario_e_valido(valor):
        # staticmethod: não recebe nem self nem cls.
        # É só uma função utilitária "morando" dentro da classe
        # porque faz sentido conceitualmente, mas não usa nada da classe.
        return valor > 0


def demo_classmethod_staticmethod():
    f1 = Funcionario("Alexandre", 6000)
    print(f1.descricao())

    # construtor alternativo via classmethod
    f2 = Funcionario.da_string("Maria, 7200")
    print(f2.descricao())

    # staticmethod chamado direto na classe, sem instanciar nada
    print(Funcionario.salario_e_valido(-100))  # False
    print(Funcionario.salario_e_valido(5000))  # True


# ---------------------------------------------------------------------------
# 3. @property — getters/setters "pythônicos"
# ---------------------------------------------------------------------------
class ContaBancaria:
    def __init__(self, saldo_inicial):
        self._saldo = saldo_inicial  # convenção: "_" = "não mexa direto"

    @property
    def saldo(self):
        # acessado como ATRIBUTO: conta.saldo (sem parênteses)
        return self._saldo

    @saldo.setter
    def saldo(self, valor):
        # permite `conta.saldo = 100` mas com validação por trás
        if valor < 0:
            raise ValueError("Saldo não pode ser negativo")
        self._saldo = valor


def demo_property():
    conta = ContaBancaria(1000)
    print(conta.saldo)      # chama o getter, sem parênteses
    conta.saldo = 1500      # chama o setter
    print(conta.saldo)
    try:
        conta.saldo = -5500   # dispara o ValueError do setter
    except ValueError as e:
        print(f"Erro esperado: {e}")


# ---------------------------------------------------------------------------
# 4. DUNDER METHODS (__init__, __repr__, __eq__, __hash__)
# ---------------------------------------------------------------------------
class Ponto:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        # usado por print(), debugger, e no shell interativo
        return f"Ponto(x={self.x}, y={self.y})"

    def __eq__(self, outro):
        # sem isso, Ponto(1,2) == Ponto(1,2) seria False (comparação por id)
        if not isinstance(outro, Ponto):
            return NotImplemented
        return self.x == outro.x and self.y == outro.y

    def __hash__(self):
        # necessário se você quiser colocar Ponto num set ou usar como
        # chave de dict. Se define __eq__, o Python "desliga" o hash
        # padrão — você tem que devolver ele explicitamente.
        return hash((self.x, self.y))

    def __add__(self, outro):
        # permite Ponto(1,1) + Ponto(2,2) -> Ponto(3,3)
        return Ponto(self.x + outro.x, self.y + outro.y)


def demo_dunder():
    p1 = Ponto(1, 2)
    p2 = Ponto(1, 2)
    p3 = Ponto(5, 5)

    print(p1)                  # usa __repr__
    print(p1 == p2)            # True, usa __eq__
    print(p1 == p3)            # False
    print(p1 + p3)             # usa __add__ -> Ponto(6, 7)
    # usa __hash__ -> p1 e p2 colapsam (são "iguais")
    print({p1, p2, p3})
