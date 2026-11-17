"""Вывод значений конфигурации в формате YAML."""

from typing import Any

import yaml

DOCUMENT_END = "...\n"
UNLIMITED_WIDTH = 2**31 - 1


class _NoAliasDumper(yaml.SafeDumper):
    """Dumper без якорей и ссылок (&id001, *id001)."""

    def ignore_aliases(self, data: Any) -> bool:
        """Всегда отключает якоря для повторяющихся объектов."""
        return True


def to_yaml(value: Any) -> str:
    """Преобразует значение в текст YAML.

    Args:
        value: float, str, list или dict (с вложенностью).

    Returns:
        Текст YAML, оканчивающийся переводом строки. Порядок ключей
        словарей сохраняется, кириллица не экранируется, длинные
        строки не переносятся.
    """
    text = yaml.dump(
        value,
        Dumper=_NoAliasDumper,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=UNLIMITED_WIDTH,
    )
    return text.removesuffix(DOCUMENT_END)
