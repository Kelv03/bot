class BaseScraper:
    def __init__(self, config=None):
        self.config = config

    def identificar_fonte(self) -> str:
        raise NotImplementedError

    def buscar_projetos(self, pagina) -> list:
        """Deve retornar uma lista de dicts padronizados."""
        raise NotImplementedError