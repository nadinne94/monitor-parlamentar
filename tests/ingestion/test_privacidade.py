import pytest

from monitor.ingestion.core.privacidade import eh_cpf, mascarar_cpf, mascarar_cpfs_no_texto


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


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("JOAO DA SILVA 12345678901", "JOAO DA SILVA ***.456.789-**"),
        ("MARIA 123.456.789-01 ME", "MARIA ***.456.789-** ME"),
        ("POSTO EXEMPLO 12.345.678/0001-99", "POSTO EXEMPLO 12.345.678/0001-99"),
        ("EMPRESA EXEMPLO 12345678000199", "EMPRESA EXEMPLO 12345678000199"),
        ("PAPELARIA CENTRAL", "PAPELARIA CENTRAL"),
    ],
)
def test_mascara_cpf_dentro_de_um_texto(texto, esperado):
    assert mascarar_cpfs_no_texto(texto) == esperado
