from rest_framework import serializers
from decimal import Decimal
from django_drf_avancado.models import Livro


class LivroRestSerializer(serializers.ModelSerializer):
    """
    Serializer próprio deste app. O nome é diferente de propósito do
    LivroSerializer do django_drf_avancado: o drf-spectacular usa o nome
    da classe como nome do componente no schema, e dois serializers com
    o mesmo nome gerariam conflito (warning) na documentação.

    O campo `autor` aparece como o ID do autor (comportamento padrão do
    ModelSerializer para ForeignKey), o que é o formato natural de
    ENTRADA numa API: o cliente manda "autor": 3.
    """

    class Meta:
        model = Livro
        fields = ['id', 'titulo', 'autor', 'ano_publicacao', 'preco']
        read_only_fields = ['id']

class PerfilSerializer(serializers.Serializer):
    """Só descreve o formato da resposta do perfil (o Swagger usa isto)."""
    id = serializers.IntegerField()
    username = serializers.CharField()
    is_staff = serializers.BooleanField()
    autenticado_via = serializers.CharField()

class LivroV2Serializer(serializers.ModelSerializer):
    """
    Formato da v2. Mudanças que QUEBRAM clientes da v1:
      - autor:  de ID (3) para objeto ({"id": 3, "nome": "..."})
      - preco:  de string ("29.90") para objeto ({"valor": "29.90", "moeda": "BRL"})
    É por isso que isso vira uma versão nova, e não um ajuste na v1.
    """

    autor = serializers.SerializerMethodField()
    preco = serializers.SerializerMethodField()

    class Meta:
        model = Livro
        fields = ['id', 'titulo', 'autor', 'ano_publicacao', 'preco']

    # O type hint de retorno (-> dict) não é enfeite: o drf-spectacular
    # lê esse hint pra descrever o campo no schema. Sem ele, aparece um
    # warning "unable to resolve type hint".
    def get_autor(self, obj) -> dict:
        # obj.autor.nome acessaria o banco a cada livro (o N+1 que você
        # já conhece). A view resolve isso com select_related('autor').
        return {'id': obj.autor_id, 'nome': obj.autor.nome}

    def get_preco(self, obj) -> dict:
        return {'valor': str(obj.preco), 'moeda': 'BRL'}

class LivroEntradaSerializer(serializers.Serializer):
    """
    Valida só o FORMATO da entrada (tipo, tamanho, obrigatório). As regras
    de negócio (ano no futuro, título duplicado) ficam no service.
    """
    titulo = serializers.CharField(max_length=200)
    autor_id = serializers.IntegerField()
    ano_publicacao = serializers.IntegerField()
    preco = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=Decimal('0.01')
    )


class DescontoEntradaSerializer(serializers.Serializer):
    percentual = serializers.IntegerField()    