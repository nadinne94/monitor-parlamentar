from datetime import date

import pytest

from monitor.ingestion.camara.proposicoes import limites_do_mes


@pytest.mark.parametrize(
    ("mes", "esperado"),
    [
        ("2026-10", (date(2026, 10, 1), date(2026, 10, 31))),
        ("2026-11", (date(2026, 11, 1), date(2026, 11, 30))),
        ("2028-02", (date(2028, 2, 1), date(2028, 2, 29))),
    ],
)
def test_limites_do_mes(mes, esperado):
    assert limites_do_mes(mes) == esperado
