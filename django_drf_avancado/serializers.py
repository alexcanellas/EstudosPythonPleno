from rest_framework import serializers
from django_drf_avancado.models import Autor, Livro


class AutorResumidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Autor
        fields = ['id', 'nome', 'nacionalidade']  # sem o campo 'livros'


class LivroSerializer(serializers.ModelSerializer):
    # StringRelatedField: mostra a representação em string do autor
    # exibe o __str__ do model Autor, que é o nome do autor. Se quisermos
    # exibir o id do autor, poderíamos usar PrimaryKeyRelatedField.   
    #autor = serializers.StringRelatedField()

    autor = AutorResumidoSerializer(read_only=True)

    class Meta:
        model = Livro
        fields = ['id', 'titulo', 'ano_publicacao', 'preco', 'autor']


class AutorSerializer(serializers.ModelSerializer):
    # nested serializer: inclui a lista de livros do autor dentro do
    # JSON do autor. many=True porque é um relacionamento "para muitos".
    # read_only=True porque aqui é só leitura (não criamos livros por
    # este serializer).
    livros = LivroSerializer(many=True, read_only=True)

    # SerializerMethodField: um campo calculado, que não existe direto
    # no model — chama get_<nome_do_campo> automaticamente
    quantidade_livros = serializers.SerializerMethodField()

    class Meta:
        model = Autor
        fields = ['id', 'nome', 'nacionalidade', 'livros', 'quantidade_livros']

    def get_quantidade_livros(self, obj):
        # `obj` aqui é a instância de Autor sendo serializada
        return obj.livros.count()

    def validate_nome(self, value):
        # validação de campo específico: DRF chama validate_<nome_do_campo>
        # automaticamente antes de salvar
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Nome precisa ter pelo menos 2 caracteres")
        return value

    def validate(self, data):
    # Só valida a nacionalidade SE ela veio no payload. Em um PATCH
    # parcial, campo ausente significa "não quero alterar", não "vazio".
        if 'nacionalidade' in data and data['nacionalidade'].strip() == '':
            raise serializers.ValidationError("Nacionalidade não pode ser vazia")
        return data
