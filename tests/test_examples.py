"""Тесты примеров конфигураций из каталога examples."""

import re
from pathlib import Path

import pytest
import yaml

from confgen.translator import translate

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
CONFIGS = sorted(EXAMPLES_DIR.glob("*.conf"))
MIN_EXAMPLES = 3

CONSTRUCT_PATTERNS = {
    "однострочный комментарий": r"(?m)^\*",
    "многострочный комментарий": r"\{\{!",
    "объявление let": r"(?m)^let \w+ = ",
    "число": r"\d+\.?\d*[eE][+-]?\d+",
    "строка": r'@"[^"]*"',
    "массив": r"#\(",
    "словарь": r"\bbegin\b",
    "вычисление": r"\^\[",
    "сложение": r"\w \+ \w",
    "вычитание": r"\w - \w",
    "умножение": r"\w \* \w",
    "деление": r"\w / \w",
    "min": r"\bmin\(",
}


def read(path: Path) -> str:
    """Читает текстовый файл в UTF-8."""
    return path.read_text(encoding="utf-8")


def load(name: str):
    """Транслирует пример и разбирает полученный YAML."""
    return yaml.safe_load(translate(read(EXAMPLES_DIR / f"{name}.conf")))


def test_at_least_three_examples():
    """В каталоге examples есть не менее трёх примеров."""
    assert len(CONFIGS) >= MIN_EXAMPLES


@pytest.mark.parametrize("conf", CONFIGS, ids=lambda path: path.stem)
def test_matches_golden_output(conf):
    """Результат трансляции совпадает с эталонным .yaml рядом."""
    expected = read(conf.with_suffix(".yaml"))
    assert translate(read(conf)) == expected


@pytest.mark.parametrize("name", CONSTRUCT_PATTERNS)
def test_examples_use_every_construct(name):
    """Каждая конструкция языка встречается хотя бы в одном примере."""
    combined = "\n".join(read(path) for path in CONFIGS)
    assert re.search(CONSTRUCT_PATTERNS[name], combined)


def test_web_service_values():
    """Значения примера веб-сервиса посчитаны верно."""
    data = load("web_service")
    ports = (data["port"], data["adminPort"], data["memoryPerWorkerMb"])
    assert ports == (8080.0, 8090.0, 128.0)
    assert data["limits"] == {"maxConnections": 400.0, "timeoutSeconds": 30.0}


def test_game_balance_values():
    """Значения примера игрового баланса посчитаны верно."""
    data = load("game_balance")
    assert data["hero"]["bonus"] == {"health": 20.0, "damage": 5.0}
    troll = {"kind": "Тролль", "health": 250.0, "damage": 25.0}
    assert data["enemies"][1] == troll
    assert data["waves"] == [[1.0, 2.0], [3.0, 5.0], []]


def test_shop_order_values():
    """Значения примера заказа посчитаны верно."""
    data = load("shop_order")
    totals = (data["subtotal"], data["discount"], data["total"])
    assert totals == (3500.0, 350.0, 3937.5)
