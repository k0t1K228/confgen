"""Исключения транслятора."""


class ConfigError(Exception):
    """Базовая ошибка обработки конфигурации с позицией в тексте."""

    def __init__(self, message: str, line: int, column: int) -> None:
        """Сохраняет текст ошибки и её позицию во входном тексте."""
        super().__init__(f"строка {line}, столбец {column}: {message}")
        self.message = message
        self.line = line
        self.column = column


class ConfigSyntaxError(ConfigError):
    """Синтаксическая ошибка во входном тексте."""


class ConfigEvalError(ConfigError):
    """Ошибка вычисления констант и выражений."""
