from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from django_drf_avancado.models import Autor, Livro


@receiver(post_save, sender=Livro)
def notificar_livro_criado(sender, instance, created, **kwargs):
    """
    Roda TODA VEZ que um Livro é salvo (criado OU atualizado).

    - sender: a classe que disparou o signal (aqui, sempre Livro)
    - instance: o objeto específico que foi salvo
    - created: True se foi um INSERT novo, False se foi um UPDATE
    """
    if created:
        print(f"  [signal] Novo livro criado: '{instance.titulo}' "
              f"de {instance.autor.nome}")
    else:
        print(f"  [signal] Livro atualizado: '{instance.titulo}'")


@receiver(pre_delete, sender=Autor)
def avisar_antes_de_deletar_autor(sender, instance, **kwargs):
    """
    Roda ANTES de um Autor ser deletado. Útil pra validações ou logs
    antes que o CASCADE apague os livros relacionados também.
    """
    qtd_livros = instance.livros.count()
    print(f"  [signal] Autor '{instance.nome}' está sendo deletado — "
          f"{qtd_livros} livro(s) serão apagados junto (CASCADE)") 