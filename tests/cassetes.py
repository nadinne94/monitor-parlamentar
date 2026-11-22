"""Anonimização das respostas gravadas nas cassetes (ver ADR-009, seção 6).

As cassetes entram no repositório, que é público. Antes de gravar uma resposta de despesas,
o CPF de fornecedor pessoa física vira um CPF fictício, e o nome e o link do comprovante
são apagados. Assim, os testes continuam exercitando o caminho da pessoa física.
"""

import json

from monitor.ingestion.core.privacidade import eh_cpf, mascarar_cpfs_no_texto

CPF_FICTICIO = "00000000000"
NOME_ANONIMO = "PESSOA FISICA ANONIMIZADA"


def anonimizar_despesas(corpo: str) -> str:
    """Troca os dados pessoais de fornecedor numa resposta de `/deputados/{id}/despesas`."""
    dados = json.loads(corpo)
    for item in dados["dados"]:
        if eh_cpf(item.get("cnpjCpfFornecedor")):
            item["cnpjCpfFornecedor"] = CPF_FICTICIO
            item["nomeFornecedor"] = NOME_ANONIMO
            item["urlDocumento"] = None
        elif item.get("nomeFornecedor"):
            item["nomeFornecedor"] = mascarar_cpfs_no_texto(item["nomeFornecedor"])
    return json.dumps(dados, ensure_ascii=False)
