"""Cliente HTTP genérico para APIs de dados abertos.

Responsável por: requisições com novas tentativas em falhas temporárias e paginação
pelo link `next`. Não conhece nenhum recurso específico (deputados, votações etc.).
"""

from typing import Any

import httpx

USER_AGENT = "monitor-parlamentar (+https://github.com/nadinne94/monitor-parlamentar)"


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
        resposta = self._http.get(caminho, params=params)
        resposta.raise_for_status()
        return resposta.json()

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "ClienteApi":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
