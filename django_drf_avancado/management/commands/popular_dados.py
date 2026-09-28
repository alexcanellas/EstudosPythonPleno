from django.core.management.base import BaseCommand
from django_drf_avancado.models import Autor, Livro


class Command(BaseCommand):
    help = 'Popula o banco com autores e livros de exemplo, pra demonstrar ORM avançado'

    def handle(self, *args, **kwargs):
        # limpa dados antigos, pra poder rodar esse comando várias vezes
        Livro.objects.all().delete()
        Autor.objects.all().delete()

        dados = [
            ('Machado de Assis', 'Brasileira', [
                ('Dom Casmurro', 1899, 29.90),
                ('Memórias Póstumas de Brás Cubas', 1881, 24.90),
                ('Quincas Borba', 1891, 27.50),
            ]),
            ('Clarice Lispector', 'Brasileira', [
                ('A Hora da Estrela', 1977, 32.00),
                ('Perto do Coração Selvagem', 1943, 34.90),
            ]),
            ('George Orwell', 'Britânica', [
                ('1984', 1949, 39.90),
                ('A Revolução dos Bichos', 1945, 22.90),
            ]),
        ]

        for nome_autor, nacionalidade, livros in dados:
            autor = Autor.objects.create(nome=nome_autor, nacionalidade=nacionalidade)
            for titulo, ano, preco in livros:
                Livro.objects.create(
                    titulo=titulo,
                    autor=autor,
                    ano_publicacao=ano,
                    preco=preco,
                )

        total_autores = Autor.objects.count()
        total_livros = Livro.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Dados criados: {total_autores} autores, {total_livros} livros'
            )
        )
        