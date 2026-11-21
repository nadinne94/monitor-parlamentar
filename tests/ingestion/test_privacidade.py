import pytest

from monitor.ingestion.core.privacidade import eh_cpf, mascarar_cpf


@pytest.mark.parametrize("cpf", ["12345678901", "123.456.789-01"])
def test_mascara_o_cpf_deixando_so_os_digitos_do_meio(cpf):
    assert mascarar_cpf(cpf) == "***.456.789-**"


@pytest.mark.parametrize("documento", ["12345678000199", "1234567890"])
def test_recusa_o_que_nao_e_cpf_sem_mostrar_o_documento(documento):
    with pytest.raises(ValueError, match="11 dígitos") as erro:
        mascarar_cpf(documento)

    assert documento not in str(erro.value)


@pytest.mark.parametrize(
    ("documento", "esperado"),
    [
        ("12345678901", True),
        ("123.456.789-01", True),
        ("12345678000199", False),
        ("", False),
        (None, False),
    ],
)
def test_reconhece_cpf_pelos_11_digitos(documento, esperado):
    assert eh_cpf(documento) is esperado
