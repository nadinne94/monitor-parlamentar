import pytest


def _ignorar_erros_do_servidor(resposta):
    """Não grava respostas 5xx: uma cassete deve guardar a API funcionando."""
    return None if resposta["status"]["code"] >= 500 else resposta


@pytest.fixture(scope="module")
def vcr_config():
    return {
        "decode_compressed_response": True,
        "before_record_response": _ignorar_erros_do_servidor,
    }
