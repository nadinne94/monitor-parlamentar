"""Cliente HTTP genérico para APIs de dados abertos.

Responsável por: requisições com novas tentativas em falhas temporárias e paginação
pelo link `next`. Não conhece nenhum recurso específico (deputados, votações etc.).
"""

from collections.abc import Iterator
from typing import Any

import httpx
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential

USER_AGENT = "monitor-parlamentar (+https://github.com/nadinne94/monitor-parlamentar)"


def eh_falha_temporaria(erro: BaseException) -> bool:
    """Falhas que valem uma nova tentativa: 429 e erros 5xx."""
    if isinstance(erro, httpx.HTTPStatusError):
        status = erro.response.status_code
        return status == 429 or status >= 500
    """Falhas que valem uma nova tentativa: rede, tempo esgotado, 429 e erros 5xx."""
    ...
    return isinstance(erro, httpx.TransportError)


class ClienteApi:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30.0,
        max_tentativas: int = 3,
        espera_inicial: float = 1.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._http = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers={"Accept": "application/json", "User-Agent": USER_AGENT},
            transport=transport,
        )
        self._max_tentativas = max_tentativas
        self._espera_inicial = espera_inicial

    def get_json(self, caminho: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """GET com novas tentativas em falhas temporárias. Erros 4xx falham na hora."""
        tentativas = Retrying(
            stop=stop_after_attempt(self._max_tentativas),
            wait=wait_exponential(multiplier=self._espera_inicial, max=30),
            retry=retry_if_exception(eh_falha_temporaria),
            reraise=True,
        )
        for tentativa in tentativas:
            with tentativa:
                resposta = self._http.get(caminho, params=params)
                resposta.raise_for_status()
                return resposta.json()
        raise AssertionError("inalcançável")  # pragma: no cover

    def paginar(self, caminho: str, params: dict[str, Any] | None = None) -> Iterator[dict]:
        """Percorre todas as páginas seguindo o link `next` e devolve cada item de `dados`."""
        corpo = self.get_json(caminho, params)
        while True:
            yield from corpo.get("dados", [])
            proxima = next(
                (link["href"] for link in corpo.get("links", []) if link.get("rel") == "next"),
                None,
            )
            if proxima is None:
                return
            corpo = self.get_json(proxima)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "ClienteApi":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
