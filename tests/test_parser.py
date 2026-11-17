"""Тесты синтаксического разбора."""

import pytest

from confgen.parser import ConfigSyntaxError, parse

SECOND_LINE = 2


def kinds(text: str) -> list[str]:
    """Возвращает имена дочерних узлов корня дерева."""
    return [child.data for child in parse(text).children]


@pytest.mark.parametrize(
    "text",
    ["1e0", "+1e0", "-1e0", "12E+3", "1.e5", "-2.5e-3", "0.5E10"],
)
def test_number_valid(text):
    """Числа с обязательной экспонентой разбираются."""
    assert kinds(text) == ["number"]


@pytest.mark.parametrize("text", ["5", "1.5", ".5e1", "1e", "e5", "1e+"])
def test_number_invalid(text):
    """Числа без экспоненты или с неверной формой отвергаются."""
    with pytest.raises(ConfigSyntaxError):
        parse(text)


def test_string():
    """Строка @"..." разбирается, в том числе пустая и многострочная."""
    assert kinds('@"Это строка"') == ["string"]
    assert kinds('@""') == ["string"]
    assert kinds('@"две\nстроки"') == ["string"]


def test_string_unterminated():
    """Незакрытая строка даёт синтаксическую ошибку."""
    with pytest.raises(ConfigSyntaxError):
        parse('@"без конца')


@pytest.mark.parametrize(
    "text",
    ["#()", "#(1e0)", '#(1e0, @"a", 2e0)', "#(#(1e0), #())"],
)
def test_array_valid(text):
    """Массивы разбираются, в том числе пустые и вложенные."""
    assert kinds(text) == ["array"]


@pytest.mark.parametrize("text", ["#(1e0 2e0)", "#(1e0,)", "#(1e0", "(1e0)"])
def test_array_invalid(text):
    """Массивы без запятых, с лишней запятой или скобкой отвергаются."""
    with pytest.raises(ConfigSyntaxError):
        parse(text)


def test_dict_valid():
    """Словари разбираются, в том числе пустые и вложенные."""
    assert kinds("begin end") == ["dict"]
    assert kinds("begin a := 1e0; end") == ["dict"]
    text = 'begin a := begin b := @"x"; end; c := #(1e0); end'
    assert kinds(text) == ["dict"]


@pytest.mark.parametrize(
    "text",
    [
        "begin a := 1e0 end",
        "begin a = 1e0; end",
        "begin := 1e0; end",
        "begin a := 1e0;",
        "begin a1 := 1e0; end",
    ],
)
def test_dict_invalid(text):
    """Словари без ';', с неверным присваиванием или именем отвергаются."""
    with pytest.raises(ConfigSyntaxError):
        parse(text)


def test_const_decl():
    """Объявления let разбираются перед итоговым значением."""
    assert kinds("let a = 1e0 let b = 2e0 3e0") == [
        "const_decl",
        "const_decl",
        "number",
    ]


@pytest.mark.parametrize(
    "text",
    ["let a = 1e0", "let a = 1e0;", "let = 1e0 2e0", "let a := 1e0 2e0"],
)
def test_const_decl_invalid(text):
    """Объявления без значения, с ';' или не тем знаком отвергаются."""
    with pytest.raises(ConfigSyntaxError):
        parse(text)


@pytest.mark.parametrize(
    "expr",
    [
        "a",
        "a + 1e0",
        "a - 1e0",
        "a * 2e0",
        "a / 2e0",
        "a *2e0",
        "a-1e0",
        "a +1e0",
        "(a + 1e0) * 2e0",
        "min(a, 1e0)",
        "min(a, 1e0, (a + 2e0) * 3e0)",
        "min(min(a, 1e0), 2e0)",
    ],
)
def test_expr_valid(expr):
    """Константные выражения в инфиксной форме разбираются."""
    assert kinds(f"let a = 1e0 ^[{expr}]") == ["const_decl", "expr"]


@pytest.mark.parametrize(
    "expr",
    ["", "a +", "a b", "min()", "min(a", "(a + 1e0", "a + * 2e0", "1"],
)
def test_expr_invalid(expr):
    """Неверные выражения отвергаются."""
    with pytest.raises(ConfigSyntaxError):
        parse(f"let a = 1e0 ^[{expr}]")


def test_expr_precedence():
    """Умножение связывает сильнее сложения."""
    tree = parse("^[a + b * c]")
    expr = tree.children[0]
    assert expr.children[0].data == "add"
    assert expr.children[0].children[1].data == "mul"


def test_expr_left_associative():
    """Вычитание левоассоциативно: a - b - c = (a - b) - c."""
    expr = parse("^[a - b - c]").children[0]
    assert expr.children[0].children[0].data == "sub"


def test_expr_as_value_in_containers():
    """Выражение может быть значением в массиве, словаре и let."""
    text = "let x = ^[1e0 + 2e0] begin a := ^[x]; b := #(^[x]); end"
    assert kinds(text) == ["const_decl", "dict"]


def test_single_line_comment():
    """Однострочные комментарии начинаются с '*' в начале строки."""
    assert kinds("* комментарий\n1e0") == ["number"]
    assert kinds("   * с отступом\n1e0") == ["number"]
    assert kinds("let a = 1e0\n* между\nbegin a := 1e0; end") == [
        "const_decl",
        "dict",
    ]


def test_multiplication_is_not_comment():
    """'*' внутри строки с выражением остаётся умножением."""
    assert kinds("^[2e0 * 3e0]") == ["expr"]


def test_block_comment():
    """Многострочные комментарии {{! ... }} игнорируются."""
    assert kinds("{{!\nмного\nстрок\n}} 1e0") == ["number"]
    assert kinds("begin {{! тут }} a := {{! и тут }} 1e0; end") == ["dict"]


def test_block_comment_unterminated():
    """Незакрытый многострочный комментарий даёт ошибку."""
    with pytest.raises(ConfigSyntaxError):
        parse("{{! без конца\n1e0")


@pytest.mark.parametrize("text", ["", "let a = 1e0", "1e0 2e0", "* только"])
def test_program_needs_exactly_one_value(text):
    """Программа без итогового значения или с лишним значением неверна."""
    with pytest.raises(ConfigSyntaxError):
        parse(text)


def test_error_position():
    """Ошибка содержит строку и столбец."""
    with pytest.raises(ConfigSyntaxError) as info:
        parse("let a = 1e0\nbegin a := ; end")
    assert info.value.line == SECOND_LINE
    assert info.value.column == len("begin a := ") + 1
    assert "строка 2" in str(info.value)


def test_error_message_lists_expected():
    """Сообщение об ошибке перечисляет ожидаемые токены."""
    with pytest.raises(ConfigSyntaxError) as info:
        parse("#(1e0 2e0)")
    assert "ожидалось" in info.value.message
    assert "','" in info.value.message


def test_error_end_of_input():
    """Неожиданный конец ввода описывается отдельно."""
    with pytest.raises(ConfigSyntaxError) as info:
        parse("let a = 1e0")
    assert "конец ввода" in info.value.message


def test_invalid_character():
    """Недопустимый символ даёт ошибку с позицией."""
    with pytest.raises(ConfigSyntaxError) as info:
        parse("begin a := 1e0; ? end")
    assert "недопустимый символ" in info.value.message
