"""Полный цикл трансляции: текст конфигурации в текст YAML."""

from confgen.emitter import to_yaml
from confgen.evaluator import evaluate
from confgen.parser import parse


def translate(text: str) -> str:
    """Переводит текст на учебном конфигурационном языке в YAML.

    Args:
        text: исходный текст конфигурации.

    Returns:
        Текст YAML.

    Raises:
        ConfigSyntaxError: при синтаксической ошибке.
        ConfigEvalError: при ошибке вычисления констант.
    """
    return to_yaml(evaluate(parse(text)))
