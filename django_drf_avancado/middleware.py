import time


class TempoDeRespostaMiddleware:
    """
    Middleware que mede quanto tempo cada requisição leva, e adiciona
    esse tempo como um header customizado na resposta.

    Todo middleware segue o mesmo formato: uma classe com __init__
    (roda UMA VEZ, quando o servidor sobe) e __call__ (roda A CADA
    requisição).
    """

    def __init__(self, get_response):
        # get_response é a "próxima camada" — pode ser outro middleware,
        # ou a view final, dependendo da posição na lista MIDDLEWARE
        self.get_response = get_response
        print("  [middleware] TempoDeRespostaMiddleware inicializado "
              "(isso roda só 1 vez, quando o servidor sobe)")

    def __call__(self, request):
        # tudo ANTES desta linha roda antes da view processar a requisição
        inicio = time.perf_counter()

        response = self.get_response(request)  # aqui a view (ou próximo middleware) roda

        # tudo DEPOIS desta linha roda depois da view responder,
        # antes da resposta voltar pro navegador
        duracao = time.perf_counter() - inicio
        response['X-Tempo-Resposta'] = f"{duracao:.4f}s"

        return response


class LogRequisicaoMiddleware:
    """
    Middleware simples que loga método + path de toda requisição que
    chega no servidor.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(f"  [middleware] {request.method} {request.path}")
        response = self.get_response(request)
        return response