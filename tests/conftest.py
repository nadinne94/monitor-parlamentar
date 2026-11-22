import pytest

from tests.cassetes import preparar_resposta


@pytest.fixture(scope="module")
def vcr_config():
    return {
        "decode_compressed_response": True,
        "before_record_response": preparar_resposta,
    }
