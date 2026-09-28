from rest_framework import permissions


class ApenasLeituraOuAutenticado(permissions.BasePermission):
    """
    Permissão customizada: qualquer um pode LER (GET/HEAD/OPTIONS),
    mas só usuário autenticado pode ESCREVER (POST/PUT/PATCH/DELETE).

    Isso é o mesmo comportamento do IsAuthenticatedOrReadOnly que já
    vem pronto no DRF — está aqui só pra você ver como é implementado
    por dentro.
    """

    def has_permission(self, request, view):
        # SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS') — métodos que não alteram dado
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class ApenasDonoOuLeitura(permissions.BasePermission):
    """
    Permissão a nível de OBJETO: qualquer um pode ler, mas só quem
    criou o registro pode editar/deletar.

    has_permission roda ANTES de saber qual objeto (nível de view).
    has_object_permission roda DEPOIS, já com o objeto em mãos — só
    é chamado se has_permission já liberou.
    """

    def has_permission(self, request, view):
        # aqui ainda não temos o objeto, só sabemos se o método é seguro
        # ou se o usuário está autenticado (pré-requisito mínimo)
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # supõe que o model tem um campo `criado_por` (não temos isso em
        # Autor/Livro ainda — isso é ilustrativo de um padrão comum)
        return getattr(obj, 'criado_por', None) == request.user
