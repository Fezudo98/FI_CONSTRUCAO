class ServiceError(Exception):
    """Erro de regra de negócio, mostrado ao usuário como está."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class InsufficientStockError(ServiceError):
    def __init__(self, product_name: str, available, requested):
        super().__init__(
            f"Estoque insuficiente de '{product_name}': disponível {available}, solicitado {requested}"
        )
