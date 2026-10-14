# ============================================================================
# ESTÁGIO 1: builder — onde as dependências são instaladas
# ============================================================================
FROM python:3.13-slim AS builder

WORKDIR /app

# Instala as dependências num diretório separado (--prefix), em vez de
# direto no Python do sistema. Isso é o que vai permitir COPIAR só essa
# pasta pro estágio final, sem levar o resto do builder junto.
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt




# ============================================================================
# ESTÁGIO 2: final — a imagem que realmente vai rodar em produção
# ============================================================================
# Começa de uma imagem NOVA, limpa — não herda nada do estágio builder
# automaticamente. Só o que for copiado explicitamente com COPY --from
# chega aqui.
FROM python:3.13-slim AS final

WORKDIR /app

# Copia SÓ as bibliotecas já instaladas do estágio builder — não o cache
# do pip, não nenhuma ferramenta de compilação que tenha sido baixada.
COPY --from=builder /install /usr/local

# Agora copia o código do projeto (isso é igual ao Dockerfile anterior)
COPY . .

# Cria um usuário NÃO-root pra rodar a aplicação. Por padrão, um
# container roda como root — se alguém explorasse uma vulnerabilidade na
# aplicação, teria privilégio total dentro do container. Rodar como um
# usuário comum reduz esse risco (princípio do menor privilégio).
RUN useradd --create-home appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
