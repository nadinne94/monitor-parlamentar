from datetime import date

import pytest

from monitor.periodos import limites_do_mes, meses_a_processar


@pytest.mark.parametrize(
    ("hoje", "esperado"),
    [
        (date(2026, 11, 8), ["2026-09", "2026-10", "2026-11"]),
        (date(2027, 1, 31), ["2026-11", "2026-12", "2027-01"]),
        (date(2027, 2, 1), ["2026-12", "2027-01", "2027-02"]),
    ],
)
def test_ultimos_tres_meses(hoje, esperado):
    assert meses_a_processar(hoje) == esperado


def test_quantidade_configuravel():
    assert meses_a_processar(date(2026, 11, 8), quantidade=1) == ["2026-11"]


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
