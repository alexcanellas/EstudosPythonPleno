# Estudos Python Pleno

Projeto de estudo para a preparação de uma vaga de Dev Pleno Python. Cada tópico é um app Django com duas partes: uma **página de documentação** (a explicação do conceito) e um **código de verdade, comentado**, que se estuda no editor e se roda no shell. A página inicial funciona como índice, com um resumo de cada tópico.

## Roteiro

| Categoria | App | O que cobre |
|---|---|---|
| 1. Python "de verdade" | `oop_avancado` | MRO, `super()`, classmethod/staticmethod, `@property`, dunder methods |
| | `estruturas_dados` | list/dict/set por dentro, Big O, benchmark com `timeit` |
| | `generators_iterators` | `yield`, `yield from`, protocolo iterator, memória |
| | `decorators` | decorators simples, com argumentos, `functools.wraps`, empilhados |
| | `context_managers` | `__enter__`/`__exit__`, `@contextmanager` |
| | `concorrencia` | GIL, threading, multiprocessing, asyncio |
| | `excecoes_typing` | hierarquia de exceções, `raise ... from`, type hints |
| 2. Frameworks web | `django_drf_avancado` | N+1, `select_related`/`prefetch_related`, serializers, permissions, signals, middleware |
| 3. Banco de dados | `banco_dados_avancado` | SQL puro vs ORM, `EXPLAIN QUERY PLAN`, índices, `select_for_update`, migration manual |
| 4. Testes | `testes_avancado` | pytest: fixtures, parametrize, mocks, unitário/integração/e2e, cobertura |
| 5. Infra e ferramentas | `infra_ferramentas` | variáveis de ambiente, cache (Redis), Git, CI/CD, Docker, Celery |
| 6. APIs e arquitetura | `apis_arquitetura` | status codes, idempotência, versionamento, JWT, OpenAPI, service layer |
| 7. Boas práticas | `boas_praticas` | SOLID, Clean Code, Factory/Singleton/Strategy |

O app `core` só serve a página inicial (o índice).

> **FastAPI** (Pydantic, dependency injection, endpoints async) faz parte da Categoria 2, mas vive em um projeto separado (`EstudosFastAPI`), com outro processo e outra porta. Ele **não** está neste repositório.

## Como rodar

Requisitos: Python 3.13 e Git. O Docker Desktop só é necessário para o Redis e o Celery.

### Localmente

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
```

Gere uma `SECRET_KEY` e cole no `.env`:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Depois:

```powershell
python manage.py migrate
python manage.py popular_dados
python manage.py runserver
```

Abra `http://127.0.0.1:8000/`. O comando `popular_dados` cria os autores e livros usados por `django_drf_avancado`, `banco_dados_avancado` e `apis_arquitetura`.

Sem Redis, o cache usa memória local. As tasks do Celery não rodam nesse modo.

### Com Docker

```powershell
docker compose up --build
```

Sobe três serviços: `web` (Django, porta 8000), `redis` (porta 6379) e `worker` (Celery). Use `--build` quando o `requirements.txt` ou o `Dockerfile` mudarem. Mudança só em código `.py` não precisa, porque o projeto é montado como volume.

Para o cache usar o Redis, preencha no `.env`:

```
CACHE_URL=redis://redis:6379/1
```

(o `docker-compose.yml` já define isso para o container `web`). Comandos dentro do container:

```powershell
docker compose exec web python manage.py migrate
docker compose exec web python manage.py shell
docker compose down
```

## Como estudar cada app

1. Abra a página do tópico no navegador (pelo índice).
2. Leia o código no editor: `exemplos.py`, ou os arquivos indicados na página.
3. Rode as funções `demo_*` no shell:

```powershell
python manage.py shell
```
```python
from oop_avancado.exemplos import *
demo_mro()
```

Os módulos de `boas_praticas` são `solid.py`, `clean_code.py` e `padroes.py`. O app `testes_avancado` é diferente: os exemplos são arquivos de teste, rodados com pytest.

Endereços úteis:

| O quê | Endereço |
|---|---|
| Índice | `/` |
| Swagger UI (OpenAPI) | `/schema/swagger-ui/` |
| API de autores e livros (Browsable API) | `/django-drf-avancado/api/autores/` |

## Variáveis de ambiente

O `.env` não é versionado. O `.env.example` lista o que o projeto aceita:

| Variável | Para quê |
|---|---|
| `SECRET_KEY` | Obrigatória, sem valor padrão: o projeto não sobe sem ela |
| `DEBUG` | `True` em desenvolvimento |
| `ALLOWED_HOSTS` | Lista separada por vírgulas |
| `DEMO_PRIORIDADE` | Usada pela demo de ordem de prioridade do `python-decouple` |
| `CACHE_URL` | Vazia usa cache em memória; com um endereço `redis://...` usa Redis |

## Testes e cobertura

```powershell
pytest -v
pytest -m unitario -v
pytest -m integracao -v
pytest -m e2e -v

coverage run -m pytest
coverage report -m
coverage html
```

O `coverage html` gera a pasta `htmlcov/`. Abra o `htmlcov/index.html` direto no navegador, pelo caminho do arquivo.

## Integração contínua

O workflow `.github/workflows/ci.yml` roda a suíte de testes e a cobertura a cada push na `main` e a cada Pull Request para a `main`, em uma máquina virtual limpa. As variáveis de ambiente do CI são definidas no próprio YAML, porque o `.env` nunca vai para o repositório.

## Observações

- As senhas que aparecem em `apis_arquitetura/exemplos.py` existem só para a demonstração de JWT, em banco local. Nunca use isso em produção.
- O banco é um `db.sqlite3` local, ignorado pelo Git. O `docker compose` usa o mesmo arquivo, por causa do volume.
- Algumas demos dependem de infraestrutura: o cache em Redis e o Celery exigem o `docker compose` de pé.