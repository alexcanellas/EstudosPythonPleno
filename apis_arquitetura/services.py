"""
SERVICES.PY: as regras de negócio.

Repara no que NÃO tem aqui: nenhum import de Django, DRF ou models. O
service não sabe o que é HTTP nem o que é ORM. Por isso dá pra testá-lo
sem banco e sem requisição.
"""

from datetime import date
from decimal import Decimal


# ---------------------------------------------------------------------------
# EXCEÇÕES DE DOMÍNIO
# ---------------------------------------------------------------------------
# O service diz O QUE deu errado, em termos de negócio. A view decide qual
# status code isso vira. Mesma ideia da hierarquia de exceções que vimos
# em excecoes_typing: a família inteira é capturável por uma classe base.

class ErroDeDominio(Exception):
    """Base de tudo que o negócio pode recusar."""


class LivroNaoEncontrado(ErroDeDominio):
    pass


class LivroDuplicado(ErroDeDominio):
    pass


class RegraDeNegocioError(ErroDeDominio):
    """Dado bem formado, mas que viola uma regra do negócio."""


class AutorNaoEncontrado(RegraDeNegocioError):
    pass


class AnoPublicacaoInvalido(RegraDeNegocioError):
    pass


class DescontoInvalido(RegraDeNegocioError):
    pass


class LivroService:
    DESCONTO_MAXIMO = 50  # percentual

    def __init__(self, livros, autores):
        # Injeção de dependência: o service usa o que recebe, sem saber se
        # é o repositório real (banco) ou um falso (memória, nos testes).
        self.livros = livros
        self.autores = autores

    def criar(self, titulo, autor_id, ano_publicacao, preco):
        if ano_publicacao > date.today().year:
            raise AnoPublicacaoInvalido(
                f'Ano {ano_publicacao} está no futuro.'
            )
        if not self.autores.existe(autor_id):
            raise AutorNaoEncontrado(f'Autor {autor_id} não existe.')
        if self.livros.existe_titulo_do_autor(titulo, autor_id):
            raise LivroDuplicado(
                f'O autor {autor_id} já tem um livro chamado "{titulo}".'
            )

        return self.livros.criar(
            titulo=titulo,
            autor_id=autor_id,
            ano_publicacao=ano_publicacao,
            preco=preco,
        )

    def aplicar_desconto(self, livro_id, percentual):
        # Valida o que não precisa de banco ANTES de ir ao banco.
        if not 1 <= percentual <= self.DESCONTO_MAXIMO:
            raise DescontoInvalido(
                f'O desconto deve ficar entre 1% e {self.DESCONTO_MAXIMO}%.'
            )

        livro = self.livros.obter(livro_id)
        if livro is None:
            raise LivroNaoEncontrado(f'Livro {livro_id} não existe.')

        # A conta é feita em Decimal desde o início (sem passar por float),
        # pelo mesmo motivo do erro de Decimal x float lá na Categoria 3.
        fator = 1 - Decimal(percentual) / 100
        novo_preco = (livro.preco * fator).quantize(Decimal('0.01'))

        # Nota: numa operação real de ler-e-alterar, o bloco todo ficaria
        # sob transaction.atomic + select_for_update (Categoria 3). Aqui
        # fica de fora de propósito, pra manter o service sem Django.
        return self.livros.atualizar_preco(livro, novo_preco)