"""Erros da ingestão, compartilhados por todas as fontes."""


class IngestaoError(Exception):
    """A API respondeu, mas o conteúdo não faz sentido para o projeto."""


class ConfiguracaoError(Exception):
    """A fonte está declarada no sources.yaml de forma incompleta ou inválida."""
