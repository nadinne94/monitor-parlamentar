import pytest

from monitor.ingestion.core.privacidade import mascarar_cpf


@pytest.mark.parametrize("cpf", ["12345678901", "123.456.789-01"])
def test_mascara_o_cpf_deixando_so_os_digitos_do_meio(cpf):
    assert mascarar_cpf(cpf) == "***.456.789-**"
