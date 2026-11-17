"""Тесты вывода в YAML."""

import pytest
import yaml

from confgen.emitter import to_yaml


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1.0, "1.0\n"),
        (-2.5, "-2.5\n"),
        ("текст", "текст\n"),
        ([], "[]\n"),
        ({}, "{}\n"),
    ],
)
def test_top_level_values(value, expected):
    """Значения верхнего уровня выводятся без маркера конца документа."""
    assert to_yaml(value) == expected


def test_nested_structure():
    """Вложенные словари и массивы выводятся блочным стилем."""
    value = {"a": 1.0, "b": [1.0, {"c": "x"}], "d": {}}
    assert to_yaml(value) == "a: 1.0\nb:\n- 1.0\n- c: x\nd: {}\n"


def test_key_order_is_preserved():
    """Порядок ключей совпадает с порядком в исходном тексте."""
    text = to_yaml({"б": 1.0, "а": 2.0, "в": 3.0})
    assert text.splitlines() == ["б: 1.0", "а: 2.0", "в: 3.0"]


def test_cyrillic_is_not_escaped():
    """Кириллица выводится как есть."""
    assert "\\u" not in to_yaml({"ключ": "значение"})


@pytest.mark.parametrize("text", ["123", "yes", "null", "", ": x"])
def test_ambiguous_strings_are_quoted(text):
    """Строки, похожие на другие типы, остаются строками."""
    assert yaml.safe_load(to_yaml(text)) == text


def test_long_string_is_not_wrapped():
    """Длинные строки не переносятся."""
    long_text = "слово " * 40
    assert len(to_yaml({"k": long_text.strip()}).splitlines()) == 1


def test_no_aliases_for_shared_objects():
    """Повторно использованные объекты не превращаются в якоря."""
    shared = [1.0]
    text = to_yaml({"a": shared, "b": shared})
    assert "&" not in text
    assert "*" not in text


@pytest.mark.parametrize(
    "value",
    [
        1e20,
        2.5e-7,
        "строка\nс переносом",
        [[1.0, 2.0], [3.0]],
        {"a": {"b": {"c": [1.0, "x", {}]}}},
    ],
)
def test_round_trip(value):
    """Результат читается обратно в исходное значение."""
    assert yaml.safe_load(to_yaml(value)) == value
