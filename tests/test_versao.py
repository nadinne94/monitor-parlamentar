from importlib.metadata import version

import monitor


def test_versao_do_pacote_igual_a_do_pyproject():
    assert monitor.__version__ == version("monitor-parlamentar")
