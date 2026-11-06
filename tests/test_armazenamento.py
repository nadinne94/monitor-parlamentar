from datetime import date

import pytest

from monitor.armazenamento import nome_no_armazenamento


@pytest.mark.parametrize(
    ("dia", "esperado"),
    [
        (None, "camara_api__deputados.parquet"),
        (date(2026, 11, 6), "camara_api__deputados__2026-11-06.parquet"),
    ],
)
def test_nome_no_armazenamento(dia, esperado):
    assert nome_no_armazenamento("camara_api", "deputados", dia) == esperado
