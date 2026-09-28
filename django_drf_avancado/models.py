from django.db import models

class Employee(models.Model):
    password = models.CharField(max_length=100)


class Autor(models.Model):
    nome = models.CharField(max_length=100)
    nacionalidade = models.CharField(max_length=50)

    def __str__(self):
        return self.nome


class Livro(models.Model):
    titulo = models.CharField(max_length=200)
    autor = models.ForeignKey(
        Autor,
        on_delete=models.CASCADE,
        related_name='livros',  # permite autor.livros.all()
    )
    ano_publicacao = models.IntegerField()
    preco = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(fields=['titulo'], name='idx_livro_titulo'),
        ]

    def __str__(self):
        return f"{self.titulo} ({self.ano_publicacao})"