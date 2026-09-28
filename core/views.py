from django.shortcuts import render

# Lista de tópicos do projeto. Conforme os apps forem sendo criados,
# basta trocar 'pronto': False -> True e preencher a 'url'.
CATEGORIAS = [
    {
        'titulo': '1. Python "de verdade"',
        'itens': [
            {
                'nome': 'OOP Avançado',
                'desc': 'Herança múltipla, MRO, super(), classmethod/staticmethod, @property, dunder methods',
                'url': '/oop-avancado/',
                'pronto': True,
                'detalhes': [
                    ('MRO e herança múltipla',
                     'Ordem de busca de métodos quando há vários pais; super() segue essa ordem, não "a classe pai" diretamente'),
                    ('classmethod / staticmethod',
                     'classmethod recebe a classe (cls), útil como construtor alternativo; staticmethod não recebe nada, é só um utilitário'),
                    ('@property', 'Expõe um método como se fosse atributo simples, com validação por trás — getter/setter "pythônico"'),
                    ('Dunder methods',
                     'Definem como o objeto se comporta com print(), ==, +, hash(), etc'),
                ],
            },
            {
                'nome': 'Estruturas de Dados Internas',
                'desc': 'Como list, dict e set funcionam por dentro, complexidade Big O',
                'url': '/estruturas-dados/',
                'pronto': True,
                'detalhes': [
                    ('list', 'Array dinâmico: acesso por índice O(1), busca "in" O(n)'),
                    ('dict / set', 'Hash table por baixo: acesso e busca O(1) em média, independente do tamanho'),
                    ('Big O', 'Entender o custo de cada operação é o que guia qual estrutura escolher'),
                ],
            },
            {
                'nome': 'Generators e Iterators',
                'desc': 'yield, yield from, generator vs list comprehension em memória',
                'url': '/generators-iterators/',
                'pronto': True,
                'detalhes': [
                    ('yield', 'Pausa e retoma a execução, economizando memória (lazy evaluation)'),
                    ('yield from', 'Delega a produção de valores pra outro iterável, sem for+yield manual'),
                    ('Protocolo iterator', '__iter__/__next__ é o que o for usa por baixo dos panos; generator já implementa isso sozinho'),
                ],
            },
            {
                'nome': 'Decorators',
                'desc': 'Decorators próprios, com argumentos, functools.wraps',
                'url': '/decorators/',
                'pronto': True,
                'detalhes': [
                    ('Decorator simples',
                     'Uma função que recebe outra função e devolve uma nova, "envolvendo" ela'),
                    ('functools.wraps', 'Preserva __name__/__doc__ da função original — sem isso, o wrapper "rouba a identidade" dela'),
                    ('Decorator com argumentos',
                     'Uma função extra que recebe o parâmetro e devolve o decorator de verdade'),
                ],
            },
            {
                'nome': 'Context Managers',
                'desc': 'with, contextlib, criação de context managers customizados',
                'url': '/context-managers/',
                'pronto': True,
                'detalhes': [
                    ('__enter__ / __exit__',
                     'Protocolo que garante liberação de recurso, mesmo se der exceção no meio'),
                    ('@contextmanager', 'Versão enxuta usando yield — antes do yield é o __enter__, depois é o __exit__'),
                ],
            },
            {
                'nome': 'Concorrência',
                'desc': 'threading, multiprocessing, asyncio e o GIL',
                'url': '/concorrencia/',
                'pronto': True,
                'detalhes': [
                    ('GIL', 'Só uma thread executa bytecode Python por vez, no CPython'),
                    ('threading', 'Não ajuda em CPU-bound (o GIL barra); ajuda MUITO em I/O-bound (o GIL é liberado na espera)'),
                    ('multiprocessing', 'Contorna o GIL de vez — cada processo tem seu próprio interpretador — ajuda em CPU-bound'),
                    ('asyncio', 'Concorrência cooperativa numa thread só, trocando de tarefa nos pontos de await — ótimo pra I/O'),
                ],
            },
            {
                'nome': 'Exceções e Type Hints',
                'desc': 'Hierarquia de exceções, exceções customizadas, typing',
                'url': '/excecoes-typing/',
                'pronto': True,
                'detalhes': [
                    ('Hierarquia de exceções',
                     'Capturar por uma classe mais genérica (ex: LookupError) pega vários tipos relacionados'),
                    ('Exceções customizadas',
                     'Carregam dados extras junto do erro, além da mensagem'),
                    ('raise ... from ...',
                     'Preserva a exceção original como causa, em vez de esconder o contexto real do erro'),
                    ('Type hints', 'Optional/Union/Generic não mudam o runtime, mas ajudam ferramentas a pegar erro antes de rodar'),
                ],
            },
        ],
    },
    {
        'titulo': '2. Frameworks web',
        'itens': [
            {
                'nome': 'Django + DRF Avançado',
                'desc': 'ORM avançado (select_related, N+1, transactions), serializers e permissions customizadas, signals, middleware',
                'url': '/django-drf-avancado/',
                'pronto': True,
                'detalhes': [
                    ('ORM avançado', 'select_related/prefetch_related resolvem o problema N+1; transaction.atomic garante tudo-ou-nada'),
                    ('Serializers customizados',
                     'Nested serializers, SerializerMethodField, validação de campo único vs objeto inteiro'),
                    ('Permissions customizadas',
                     'has_permission (nível view, roda antes) vs has_object_permission (nível objeto, roda depois)'),
                    ('Signals', 'Reagem a eventos do ORM (post_save, pre_delete) sem acoplar a lógica dentro do save() do model'),
                    ('Middleware', 'Roda em toda requisição, antes da view processar e depois dela responder'),
                ],
            },
            {
                'nome': 'FastAPI',
                'desc': 'Pydantic, dependency injection, endpoints async — projeto separado (EstudosFastAPI, rodar na porta 8001: uvicorn main:app --reload --port 8001)',
                'url': 'http://127.0.0.1:8001/',
                'pronto': True,
                'detalhes': [
                    ('Pydantic Avançado', 'BaseModel valida automaticamente pelos type hints; Field adiciona restrições; field_validator cobre regras que Field não alcança'),
                    ('Dependency Injection', 'Depends() executa uma função antes do endpoint e injeta o resultado; encadeável (sub-dependências), base de autenticação/autorização'),
                    ('Async Endpoints', 'async def + await só ajuda em I/O; CPU pesada não ganha nada; time.sleep() dentro de async def bloqueia o event loop inteiro'),
                ],
            },
        ],
    },
    {
        'titulo': '3. Banco de Dados',
        'itens': [
            {
                'nome': 'SQL Avançado e Query Plan',
                'desc': 'SQL puro vs ORM, EXPLAIN QUERY PLAN, índices, transações e isolamento, migrations manuais',
                'url': '/banco-dados-avancado/',
                'pronto': True,
                'detalhes': [
                    ('SQL puro vs ORM', 'O ORM sempre vira SQL por trás — entender o SQL gerado ajuda a "ler" o que o ORM está fazendo'),
                    ('EXPLAIN QUERY PLAN', 'SCAN = varredura completa da tabela (lento); SEARCH = usou índice pra pular direto pro dado (rápido)'),
                    ('Índices', 'Aceleram leitura, mas custam em toda escrita (o índice também precisa ser atualizado)'),
                    ('Transações e isolamento',
                     'select_for_update trava a linha no banco, evitando race condition entre transações simultâneas'),
                    ('Migration manual', 'Escrita na mão (--empty), pra entender o que o makemigrations gera automaticamente'),
                ],
            },
        ],
    },
    {
        'titulo': '4. Testes',
        'itens': [
            {
                'nome': 'Testes Avançados (pytest)',
                'desc': 'Fixtures, parametrize, mocks, unitário vs integração vs e2e, cobertura de código',
                'url': '/testes-avancado/',
                'pronto': True,
                'detalhes': [
                    ('Fixtures', 'Preparam dados/dependências reutilizáveis; podem depender umas das outras e ter escopo (function/session/etc)'),
                    ('yield em fixture', 'Tudo antes do yield é setup, tudo depois é teardown — roda mesmo se o teste falhar'),
                    ('parametrize', 'Roda o mesmo teste várias vezes, com entradas diferentes, sem duplicar código'),
                    ('Mocks', 'Simulam uma dependência externa (API, banco lento) sem chamá-la de verdade'),
                    ('Unitário vs Integração vs E2E',
                     'Granularidade do que cada teste verifica — de uma função isolada até o sistema inteiro'),
                    ('Cobertura de código',
                     'Mede quanto do código é de fato exercitado pelos testes'),
                ],
            },
        ],
    },
    {
        'titulo': '5. Infra e Ferramentas',
        'itens': [
            {
                'nome': 'Infra e Ferramentas',
                'desc': 'Variáveis de ambiente, cache, Git, CI/CD, Docker, Celery',
                'url': '/infra-ferramentas/',
                'pronto': True,
                'detalhes': [
                    ('Variáveis de ambiente e segredos',
                     'Configuração e segredos ficam fora do código (.env, nunca versionado); o .env.example documenta o que precisa existir; python-decouple lê e converte os tipos'),
                    ('Cache', 'Cache-aside: busca no cache, e se não achar busca na fonte e guarda o resultado. O difícil é a invalidação: o dado em cache pode ficar velho'),
                    ('Git', 'merge preserva o histórico como aconteceu (com commit de merge); rebase reescreve os commits por cima da base, deixando o histórico linear. Nunca em branch compartilhada'),
                    ('CI/CD', 'CI roda os testes automaticamente a cada push ou PR; CD entrega o que passou. O workflow do GitHub Actions é um YAML versionado junto do código'),
                    ('Docker', 'O Dockerfile descreve a imagem, o docker-compose sobe vários serviços juntos, e o multi-stage build separa build de runtime para reduzir a imagem final'),
                    ('Celery + Redis', 'Tarefas demoradas saem da requisição: a view enfileira a task no broker (Redis) e um worker a executa em segundo plano'),
                ],
            },
        ],
    },
]


def index(request):
    return render(request, 'core/index.html', {'categorias': CATEGORIAS})
