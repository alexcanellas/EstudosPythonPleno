"""
REPOSITORIES.PY: acesso a dados. Só queries, nenhuma regra de negócio.

Se um dia o armazenamento mudar (outro banco, uma API externa), só este
arquivo muda. O service continua igual.
"""

from django_drf_avancado.models import Autor, Livro


class AutorRepository:
    def existe(self, autor_id):
        return Autor.objects.filter(pk=autor_id).exists()


class LivroRepository:
    def obter(self, pk):
        # Devolve None quando não existe. QUEM decide que isso é um erro
        # é o service, não o repositório.
        return Livro.objects.select_related('autor').filter(pk=pk).first()

    def existe_titulo_do_autor(self, titulo, autor_id):
        return Livro.objects.filter(titulo__iexact=titulo, autor_id=autor_id).exists()

    def criar(self, **dados):
        return Livro.objects.create(**dados)

    def atualizar_preco(self, livro, novo_preco):
        livro.preco = novo_preco
        livro.save(update_fields=['preco'])
        return livro