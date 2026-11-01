from datetime import date, datetime

import pytest

from monitor.site.gerador import formatar_data_hora, formatar_mes


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (date(2027, 2, 1), "fevereiro de 2027"),
        (date(2027, 3, 1), "março de 2027"),
        (date(2026, 12, 1), "dezembro de 2026"),
    ],
)
def test_formatar_mes(valor, esperado):
    assert formatar_mes(valor) == esperado


def test_formatar_data_hora():
    assert formatar_data_hora(datetime(2027, 3, 5, 9, 30)) == "05/03/2027 às 09:30"
