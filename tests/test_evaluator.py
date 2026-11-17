"""Тесты вычисления констант и выражений."""

import pytest

from confgen.errors import ConfigEvalError
from confgen.evaluator import evaluate
from confgen.parser import parse

SECOND_LINE = 2


def run(text: str):
    """Разбирает и вычисляет текст конфигурации."""
    return evaluate(parse(text))


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1e0", 1.0),
        ("-2.5e1", -25.0),
        ("1.e2", 100.0),
        ('@"Это строка"', "Это строка"),
        ('@""', ""),
    ],
)
def test_scalars(text, expected):
    """Числа становятся float, строки теряют обрамление."""
    assert run(text) == expected


def test_arrays():
    """Массивы вычисляются, в том числе пустые и вложенные."""
    assert run("#()") == []
    assert run('#(1e0, @"a", #(2e0, #()))') == [1.0, "a", [2.0, []]]


def test_dicts():
    """Словари вычисляются, порядок ключей сохраняется."""
    assert run("begin end") == {}
    text = 'begin b := 1e0; a := begin c := #(@"x"); end; end'
    result = run(text)
    assert result == {"b": 1.0, "a": {"c": ["x"]}}
    assert list(result) == ["b", "a"]


def test_const_usage():
    """Константы можно использовать в выражениях и объявлять по цепочке."""
    text = "let a = 2e0 let b = ^[a * 3e0] ^[b + a]"
    expected = 8.0
    assert run(text) == expected


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        ("1e0 + 2e0", 3.0),
        ("5e0 - 7e0", -2.0),
        ("3e0 * 4e0", 12.0),
        ("9e0 / 2e0", 4.5),
        ("1e0 + 2e0 * 3e0", 7.0),
        ("(1e0 + 2e0) * 3e0", 9.0),
        ("10e0 - 3e0 - 2e0", 5.0),
        ("8e0 / 2e0 / 2e0", 2.0),
        ("2e0 +3e0", 5.0),
        ("2e0-3e0", -1.0),
        ("min(4e0, 2e0, 3e0)", 2.0),
        ("min(5e0)", 5.0),
        ("min(1e0 + 5e0, 2e0 * 2e0)", 4.0),
        ("min(min(3e0, 1e0), 2e0) + 1e0", 2.0),
    ],
)
def test_expressions(expr, expected):
    """Арифметика, приоритеты, скобки и min() работают верно."""
    assert run(f"^[{expr}]") == expected


def test_expression_values_in_containers():
    """Выражения работают внутри let, массивов и словарей."""
    text = """
    let x = ^[1e0 + 1e0]
    begin
      a := ^[x * 2e0];
      b := #(^[x], ^[x + 1e0]);
      c := begin d := ^[min(x, 9e0)]; end;
    end
    """
    assert run(text) == {
        "a": 4.0,
        "b": [2.0, 3.0],
        "c": {"d": 2.0},
    }


def test_constant_of_any_type_can_be_referenced():
    """^[имя] возвращает строку, массив или словарь как есть."""
    text = (
        'let s = @"текст" let a = #(1e0) let d = begin k := 1e0; end '
        "#(^[s], ^[a], ^[d])"
    )
    assert run(text) == ["текст", [1.0], {"k": 1.0}]


def test_references_are_independent_copies():
    """Каждое обращение к константе даёт независимую копию."""
    result = run("let a = #(1e0) begin x := ^[a]; y := ^[a]; end")
    assert result["x"] == result["y"]
    assert result["x"] is not result["y"]


def test_comments_do_not_affect_result():
    """Комментарии не влияют на результат."""
    text = "* начало\nlet a = 1e0 {{! заметка }}\n^[a + 1e0]"
    expected = 2.0
    assert run(text) == expected


@pytest.mark.parametrize(
    ("text", "fragment"),
    [
        ("^[a]", "не объявлена"),
        ("let a = 1e0 ^[b + a]", "'b'"),
        ("let a = 1e0 let a = 2e0 ^[a]", "уже объявлена"),
        ("begin a := 1e0; a := 2e0; end", "повторяющийся ключ"),
        ("^[1e0 / 0e0]", "деление на ноль"),
        ("^[1e0 / (2e0 - 2e0)]", "деление на ноль"),
        ('let s = @"x" ^[s + 1e0]', "должен быть числом"),
        ("let a = #(1e0) ^[min(a, 1e0)]", "должен быть числом"),
        ("^[1e308 * 1e308]", "конечным"),
    ],
)
def test_evaluation_errors(text, fragment):
    """Ошибки вычисления сообщают причину."""
    with pytest.raises(ConfigEvalError) as info:
        run(text)
    assert fragment in info.value.message


def test_error_position():
    """Ошибка вычисления указывает на проблемный узел."""
    text = "let a = 1e0\n^[a /\n 0e0]"
    with pytest.raises(ConfigEvalError) as info:
        run(text)
    assert info.value.line == SECOND_LINE + 1
    assert "строка 3" in str(info.value)


def test_undefined_name_position():
    """Для неизвестной константы указана позиция имени."""
    with pytest.raises(ConfigEvalError) as info:
        run("let a = 1e0\n^[a + zzz]")
    assert info.value.line == SECOND_LINE
    assert info.value.column == len("^[a + ") + 1
