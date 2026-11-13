"""Excepciones de ingesta de archivos."""


class ArchivoNoSoportado(Exception):
    def __init__(self, tipo: str) -> None:
        self.tipo = tipo
        super().__init__(f"Tipo de archivo no soportado: {tipo}")


class ArchivoCorrupto(Exception):
    def __init__(self, detalle: str = "") -> None:
        self.detalle = detalle
        super().__init__(f"Archivo corrupto: {detalle}")


class ArchivoProtegido(Exception):
    def __init__(self, detalle: str = "") -> None:
        self.detalle = detalle
        super().__init__(f"Archivo protegido con contraseña: {detalle}")


class LimiteExcedido(Exception):
    def __init__(self, detalle: str = "") -> None:
        self.detalle = detalle
        super().__init__(f"Límite excedido: {detalle}")
