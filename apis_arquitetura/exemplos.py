"""
APIS E ARQUITETURA: o JWT por dentro.

Rode no shell:

    from apis_arquitetura.exemplos import *
    criar_usuarios_demo()
    demo_anatomia_do_jwt()
    demo_adulterar_jwt()
    demo_expiracao()
"""

import base64
import json
from datetime import datetime, timedelta, timezone

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

# Só pra estudo, em banco local. Senha escrita no código nunca é prática
# de produção (lembra do tópico de variáveis de ambiente).
SENHA_DEMO = 'senha-de-estudo-123'


def criar_usuarios_demo():
    """Cria (ou reaproveita) um usuário comum e um admin."""
    User = get_user_model()
    for username, eh_admin in (('dev_jwt', False), ('admin_jwt', True)):
        usuario, criado = User.objects.get_or_create(username=username)
        usuario.is_staff = eh_admin
        usuario.is_superuser = eh_admin
        usuario.set_password(SENHA_DEMO)
        usuario.save()
        papel = 'admin' if eh_admin else 'comum'
        situacao = 'criado' if criado else 'já existia, senha redefinida'
        print(f"  {username} ({papel}): {situacao}")


def _decodificar_parte(parte):
    # O JWT usa base64 "url-safe" SEM o padding "=". O decodificador
    # exige o padding, então recolocamos.
    preenchida = parte + '=' * (-len(parte) % 4)
    return json.loads(base64.urlsafe_b64decode(preenchida))


def _codificar_parte(dados):
    bruto = json.dumps(dados, separators=(',', ':')).encode()
    return base64.urlsafe_b64encode(bruto).rstrip(b'=').decode()


# ---------------------------------------------------------------------------
# 1. ANATOMIA: um JWT são três partes separadas por pontos
# ---------------------------------------------------------------------------
#   cabeçalho.carga.assinatura
# As duas primeiras são só JSON em base64, LEGÍVEIS por qualquer pessoa.
# Base64 é codificação, não criptografia.

def demo_anatomia_do_jwt():
    usuario = get_user_model().objects.get(username='dev_jwt')
    token = str(RefreshToken.for_user(usuario).access_token)
    cabecalho, carga, assinatura = token.split('.')

    print(f"Token com {len(token)} caracteres:\n  {token[:70]}...\n")

    print("1) CABEÇALHO (o algoritmo de assinatura):")
    print(f"  {_decodificar_parte(cabecalho)}\n")

    dados = _decodificar_parte(carga)
    print("2) CARGA (as 'claims', ou seja, as afirmações sobre o usuário):")
    for chave, valor in dados.items():
        print(f"  {chave}: {valor}")
    expira = datetime.fromtimestamp(dados['exp'], timezone.utc)
    print(f"  (exp em data legível: {expira:%d/%m/%Y %H:%M:%S} UTC)\n")

    print(f"3) ASSINATURA: {assinatura[:24]}...")
    print("  Calculada sobre cabeçalho+carga usando a SECRET_KEY do projeto.\n")

    print("Qualquer um lê a carga: nunca ponha senha ou segredo dentro de um JWT.")
    print("A assinatura garante INTEGRIDADE (ninguém alterou), não sigilo.")


# ---------------------------------------------------------------------------
# 2. ADULTERAÇÃO: por que a assinatura importa
# ---------------------------------------------------------------------------
# Um atacante consegue editar a carga (é só base64), mas não consegue
# recalcular a assinatura sem a SECRET_KEY. O servidor refaz o cálculo, e
# se não bater, rejeita.

def demo_adulterar_jwt():
    User = get_user_model()
    comum = User.objects.get(username='dev_jwt')
    admin = User.objects.get(username='admin_jwt')

    original = str(RefreshToken.for_user(comum).access_token)
    cabecalho, carga, assinatura = original.split('.')

    AccessToken(original)  # se fosse inválido, levantaria TokenError aqui
    print(f"Token original (user_id={_decodificar_parte(carga)['user_id']}): VÁLIDO\n")

    # O atacante troca o user_id pelo do admin, mas só tem a assinatura antiga.
    dados = _decodificar_parte(carga)
    dados['user_id'] = admin.id
    adulterado = '.'.join([cabecalho, _codificar_parte(dados), assinatura])
    print(f"Atacante muda o user_id para {admin.id} (o admin) e reaproveita a assinatura.")

    try:
        AccessToken(adulterado)
        print("Token adulterado: VÁLIDO  <- se aparecer isto, algo está muito errado")
    except TokenError as erro:
        print(f"Token adulterado: REJEITADO ({erro})")

    print("\nConexão com o tópico de segredos: quem tem a SECRET_KEY consegue")
    print("assinar qualquer token que quiser. Chave vazada = todos os tokens")
    print("do sistema deixam de ser confiáveis.")


# ---------------------------------------------------------------------------
# 3. EXPIRAÇÃO: o preço de ser stateless
# ---------------------------------------------------------------------------
# O servidor não guarda estado, então não há o que "apagar" pra revogar um
# access token. Ele só deixa de valer quando o `exp` passa. Por isso o
# access é curto, e o refresh (que dura mais) é o que se protege melhor.

def demo_expiracao():
    usuario = get_user_model().objects.get(username='dev_jwt')

    token = AccessToken.for_user(usuario)
    token.set_exp(lifetime=-timedelta(seconds=10))  # força o exp 10s no passado
    vencido = str(token)

    try:
        AccessToken(vencido)
        print("Token vencido: VÁLIDO  <- se aparecer isto, algo está errado")
    except TokenError as erro:
        print(f"Token vencido: REJEITADO ({erro})")

    print("\nPra invalidar um token ANTES do exp existe a blacklist: o servidor")
    print("passa a guardar os tokens revogados. Mas aí o JWT deixa de ser")
    print("100% stateless, e é esse o trade-off em relação à sessão.")