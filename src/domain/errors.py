"""Erros de negócio do WMS.

Cada erro carrega um código estável (para o cliente e para os testes),
uma mensagem e o status HTTP que a API deve devolver.
"""


class DomainError(Exception):
    def __init__(self, code: str, message: str, status: int = 409):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def not_found(code: str, message: str) -> DomainError:
    return DomainError(code, message, status=404)
