"""
APIS_ARQUITETURA: status codes corretos e idempotência.

Os endpoints desta demo usam authentication_classes = [] e
permission_classes = [] de propósito: ficam abertos pra você testar
direto no Swagger. Autenticação é o próximo tópico.
"""

import hashlib
import json

from django.core.cache import cache
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.versioning import URLPathVersioning

from django_drf_avancado.models import Livro

from apis_arquitetura.repositories import AutorRepository, LivroRepository
from apis_arquitetura.serializers import (
    DescontoEntradaSerializer,
    LivroEntradaSerializer,
    LivroRestSerializer,
    LivroV2Serializer,
    PerfilSerializer,
)

from apis_arquitetura.services import (
    ErroDeDominio,
    LivroDuplicado,
    LivroNaoEncontrado,
    LivroService,
    RegraDeNegocioError,
)


def index(request):
    return render(request, 'apis_arquitetura/index.html')


# Quanto tempo uma Idempotency-Key fica "lembrada". Passado esse prazo, a
# mesma chave volta a ser tratada como uma requisição nova.
IDEMPOTENCY_TTL = 60 * 60 * 24  # 24 horas

# Declara o header no schema pra ele aparecer como campo no Swagger.
PARAMETRO_IDEMPOTENCY_KEY = OpenApiParameter(
    name='Idempotency-Key',
    type=str,
    location=OpenApiParameter.HEADER,
    required=False,
    description=(
        'Identificador único gerado pelo CLIENTE para esta operação. '
        'Repetir a requisição com a mesma chave devolve a resposta '
        'original, sem criar um segundo registro.'
    ),
)


class LivroListaView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(responses={200: LivroRestSerializer(many=True)})
    def get(self, request):
        livros = Livro.objects.all().order_by('id')
        # 200 OK é o padrão do Response() quando não se passa status.
        return Response(LivroRestSerializer(livros, many=True).data)

    @extend_schema(
        request=LivroRestSerializer,
        parameters=[PARAMETRO_IDEMPOTENCY_KEY],
        responses={
            201: LivroRestSerializer,
            400: OpenApiResponse(description='Dados inválidos'),
            409: OpenApiResponse(
                description='Idempotency-Key reutilizada com um corpo diferente'
            ),
        },
    )
    def post(self, request):
        chave = request.headers.get('Idempotency-Key')
        impressao = self._impressao_digital(request.data)

        # --- Parte idempotente: só roda se o cliente mandou a chave ---
        if chave:
            guardado = cache.get(self._chave_cache(chave))

            if guardado is not None:
                # Mesma chave com um corpo DIFERENTE é erro do cliente: ele
                # está reaproveitando um identificador pra outra operação.
                # 409 Conflict comunica "isto colide com o estado atual".
                if guardado['impressao'] != impressao:
                    return Response(
                        {'detail': 'Idempotency-Key já usada com um corpo diferente.'},
                        status=status.HTTP_409_CONFLICT,
                    )

                # Mesma chave, mesmo corpo: é uma repetição. Devolve a
                # resposta ORIGINAL, sem tocar no banco de novo.
                resposta = Response(guardado['corpo'], status=guardado['status'])
                resposta['Location'] = guardado['location']
                resposta['Idempotent-Replayed'] = 'true'  # avisa que é um replay
                return resposta

        # --- Criação normal ---
        serializer = LivroRestSerializer(data=request.data)
        # raise_exception=True: se inválido, o DRF responde 400 sozinho,
        # com o detalhe de cada campo. Esta linha é o "400 Bad Request".
        serializer.is_valid(raise_exception=True)
        livro = serializer.save()

        corpo = dict(LivroRestSerializer(livro).data)

        # Location: o header que diz ONDE o novo recurso passou a existir.
        # Faz parte do contrato de um 201 Created bem feito.
        location = request.build_absolute_uri(
            reverse('apis_arquitetura:livro-detalhe', args=[livro.pk])
        )

        if chave:
            # Só guardamos respostas de SUCESSO: se a requisição falhou
            # por dado inválido, o cliente pode corrigir e tentar de novo
            # com a mesma chave.
            #
            # Limitação conhecida: duas requisições SIMULTÂNEAS com a mesma
            # chave podem passar juntas pelo cache.get acima, antes de
            # qualquer uma gravar. Em produção a chave é reservada de forma
            # atômica (cache.add ou lock) antes de processar.
            cache.set(
                self._chave_cache(chave),
                {
                    'impressao': impressao,
                    'corpo': corpo,
                    'status': status.HTTP_201_CREATED,
                    'location': location,
                },
                timeout=IDEMPOTENCY_TTL,
            )

        resposta = Response(corpo, status=status.HTTP_201_CREATED)
        resposta['Location'] = location
        return resposta

    @staticmethod
    def _chave_cache(chave):
        # Mesma convenção "entidade:id" que usamos no tópico de cache.
        return f'idempotency:{chave}'

    @staticmethod
    def _impressao_digital(dados):
        # Resumo (hash) do corpo da requisição, pra detectar se a mesma
        # chave está sendo usada com um conteúdo diferente.
        # sort_keys=True: a ordem dos campos no JSON não pode mudar o hash.
        texto = json.dumps(dados, sort_keys=True, default=str)
        return hashlib.sha256(texto.encode()).hexdigest()


class LivroDetalheView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        responses={
            200: LivroRestSerializer,
            404: OpenApiResponse(description='Livro não encontrado'),
        }
    )
    def get(self, request, pk):
        # get_object_or_404 levanta Http404, e o DRF converte isso em uma
        # resposta 404 em JSON automaticamente.
        livro = get_object_or_404(Livro, pk=pk)
        return Response(LivroRestSerializer(livro).data)

    @extend_schema(
        request=LivroRestSerializer,
        responses={
            200: LivroRestSerializer,
            400: OpenApiResponse(description='Dados inválidos'),
            404: OpenApiResponse(description='Livro não encontrado'),
        },
    )
    def put(self, request, pk):
        # PUT = SUBSTITUIÇÃO COMPLETA do recurso: o cliente manda todos os
        # campos, e o estado final depende só do que foi enviado, não do
        # estado anterior. Por isso repetir o mesmo PUT N vezes deixa o
        # servidor exatamente igual: é idempotente.
        #
        # (PATCH, a atualização parcial, NÃO é idempotente por definição:
        # um PATCH do tipo "some 1 ao estoque" muda o resultado a cada
        # repetição.)
        livro = get_object_or_404(Livro, pk=pk)
        serializer = LivroRestSerializer(livro, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(
        responses={
            204: OpenApiResponse(description='Removido com sucesso'),
            404: OpenApiResponse(description='Livro não encontrado'),
        }
    )
    def delete(self, request, pk):
        livro = get_object_or_404(Livro, pk=pk)
        livro.delete()
        # 204 No Content: deu certo e não há corpo pra devolver.
        return Response(status=status.HTTP_204_NO_CONTENT) 


# ---------------------------------------------------------------------------
# AUTENTICAÇÃO COM JWT
# ---------------------------------------------------------------------------
# A autenticação é declarada POR VIEW (authentication_classes) e não no
# settings, pra não alterar o comportamento dos outros apps do projeto.
#
# Dois conceitos separados:
#   authentication_classes -> QUEM é você? (lê o header Authorization,
#                             valida a assinatura e a expiração do token)
#   permission_classes     -> o que você PODE fazer?

def _dados_do_usuario(request):
    return {
        'id': request.user.id,
        'username': request.user.username,
        'is_staff': request.user.is_staff,
        'autenticado_via': 'JWT',
    }


class PerfilView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: PerfilSerializer,
            401: OpenApiResponse(description='Token ausente, inválido ou expirado'),
        }
    )
    def get(self, request):
        # Quando a execução chega aqui, o JWTAuthentication já leu o
        # header "Authorization: Bearer <token>", validou a assinatura e a
        # expiração, e preencheu request.user. A view não valida nada.
        return Response(_dados_do_usuario(request))


class SomenteAdminView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]  # exige is_staff=True

    @extend_schema(
        responses={
            200: PerfilSerializer,
            401: OpenApiResponse(description='Token ausente, inválido ou expirado'),
            403: OpenApiResponse(description='Autenticado, mas sem permissão'),
        }
    )
    def get(self, request):
        # Sem token: 401. Token válido de usuário comum: 403.
        #
        # Detalhe do DRF: ele só responde 401 (e não 403) quando a
        # primeira classe de autenticação sabe montar o header
        # WWW-Authenticate. O JWTAuthentication sabe; o
        # SessionAuthentication não, e por isso APIs só com sessão
        # costumam devolver 403 até pra quem não está logado.
        return Response(_dados_do_usuario(request))    


# ---------------------------------------------------------------------------
# VERSIONAMENTO PELA URL
# ---------------------------------------------------------------------------

class VersionamentoPorURL(URLPathVersioning):
    # Lista fechada de versões aceitas. Qualquer outra (ex: v3) é
    # recusada com 404 ANTES de a view rodar.
    allowed_versions = ['v1', 'v2']
    default_version = 'v1'
    version_param = 'version'  # nome do trecho <str:version> no urls.py


class LivroVersionadoView(APIView):
    authentication_classes = []
    permission_classes = []
    versioning_class = VersionamentoPorURL

    # Cada versão tem o seu serializer. A view é uma só.
    SERIALIZERS = {
        'v1': LivroRestSerializer,
        'v2': LivroV2Serializer,
    }

    @extend_schema(
        responses={
            200: LivroRestSerializer(many=True),
            404: OpenApiResponse(description='Versão inexistente'),
        }
    )
    def get(self, request, version):
        # request.version foi preenchido pelo DRF a partir do <str:version>
        # da URL, antes de esta função rodar.
        # select_related: o serializer da v2 acessa livro.autor.
        livros = Livro.objects.select_related('autor').order_by('id')
        serializer_class = self.SERIALIZERS[request.version]
        resposta = Response(serializer_class(livros, many=True).data)

        if request.version == 'v1':
            # Deprecação anunciada no PRÓPRIO header, pro cliente (ou a
            # ferramenta de monitoramento dele) perceber sem ler e-mail:
            #   Deprecation: esta versão está obsoleta
            #   Sunset:      data em que ela deixa de funcionar
            resposta['Deprecation'] = 'true'
            resposta['Sunset'] = 'Thu, 31 Dec 2026 23:59:59 GMT'

        return resposta

# ---------------------------------------------------------------------------
# SERVICE LAYER: a view só traduz HTTP
# ---------------------------------------------------------------------------

def montar_livro_service():
    # O único lugar que escolhe os repositórios REAIS. Nos testes, o
    # service é montado direto, com repositórios falsos.
    return LivroService(livros=LivroRepository(), autores=AutorRepository())


# Erro de domínio -> status code. A ordem importa: do mais específico pro
# mais genérico, porque o isinstance casa a família inteira.
STATUS_POR_ERRO = [
    (LivroNaoEncontrado, status.HTTP_404_NOT_FOUND),
    (LivroDuplicado, status.HTTP_409_CONFLICT),
    (RegraDeNegocioError, status.HTTP_422_UNPROCESSABLE_ENTITY),
    (ErroDeDominio, status.HTTP_400_BAD_REQUEST),  # rede de segurança
]


def _resposta_de_erro(erro):
    for classe, codigo in STATUS_POR_ERRO:
        if isinstance(erro, classe):
            return Response({'detail': str(erro)}, status=codigo)


class LivroCamadasView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        request=LivroEntradaSerializer,
        responses={
            201: LivroRestSerializer,
            400: OpenApiResponse(description='Formato inválido (campo faltando, tipo errado)'),
            409: OpenApiResponse(description='Livro duplicado para este autor'),
            422: OpenApiResponse(description='Formato ok, mas viola uma regra de negócio'),
        },
    )
    def post(self, request):
        entrada = LivroEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)  # 400: problema de FORMATO

        try:
            livro = montar_livro_service().criar(**entrada.validated_data)
        except ErroDeDominio as erro:
            return _resposta_de_erro(erro)  # 409 / 422: problema de NEGÓCIO

        return Response(LivroRestSerializer(livro).data, status=status.HTTP_201_CREATED)


class LivroDescontoView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        request=DescontoEntradaSerializer,
        responses={
            200: LivroRestSerializer,
            400: OpenApiResponse(description='Formato inválido'),
            404: OpenApiResponse(description='Livro não encontrado'),
            422: OpenApiResponse(description='Desconto fora da faixa permitida'),
        },
    )
    def post(self, request, pk):
        entrada = DescontoEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        try:
            livro = montar_livro_service().aplicar_desconto(
                pk, entrada.validated_data['percentual']
            )
        except ErroDeDominio as erro:
            return _resposta_de_erro(erro)

        return Response(LivroRestSerializer(livro).data)