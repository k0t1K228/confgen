"""Синтаксический разбор учебного конфигурационного языка."""

from pathlib import Path

from lark import Lark, Tree
from lark.exceptions import (
    UnexpectedCharacters,
    UnexpectedInput,
    UnexpectedToken,
)

from confgen.errors import ConfigSyntaxError

GRAMMAR_PATH = Path(__file__).with_name("grammar.lark")

END_OF_INPUT = "$END"

TERMINAL_NAMES = {
    "NUMBER": "число",
    "STRING": "строка",
    "NAME": "имя",
    "_LET": "'let'",
    "_BEGIN": "'begin'",
    "_END": "'end'",
    "_MIN": "'min'",
    "_ASSIGN": "':='",
    "_EQ": "'='",
    "_SEMI": "';'",
    "_COMMA": "','",
    "_LARR": "'#('",
    "_LEXPR": "'^['",
    "_RBRACK": "']'",
    "_LPAR": "'('",
    "_RPAR": "')'",
    "_PLUS": "'+'",
    "_MINUS": "'-'",
    "_STAR": "'*'",
    "_SLASH": "'/'",
    END_OF_INPUT: "конец ввода",
}


_PARSER = Lark.open(
    str(GRAMMAR_PATH),
    parser="lalr",
    start="start",
    maybe_placeholders=False,
    propagate_positions=True,
)


def _describe_expected(terminals: set[str]) -> str:
    """Формирует читаемый список ожидаемых токенов."""
    names = sorted(TERMINAL_NAMES.get(name, name) for name in terminals)
    return ", ".join(names)


def _token_error(err: UnexpectedToken) -> ConfigSyntaxError:
    """Преобразует ошибку неожиданного токена в ConfigSyntaxError."""
    if err.token.type == END_OF_INPUT:
        found = "неожиданный конец ввода"
    else:
        found = f"неожиданный токен '{err.token}'"
    expected = _describe_expected(err.expected)
    message = f"{found}, ожидалось: {expected}"
    return ConfigSyntaxError(message, err.line, err.column)


def _char_error(err: UnexpectedCharacters) -> ConfigSyntaxError:
    """Преобразует ошибку неожиданного символа в ConfigSyntaxError."""
    message = f"недопустимый символ {err.char!r}"
    return ConfigSyntaxError(message, err.line, err.column)


def parse(text: str) -> Tree:
    """Разбирает текст на учебном конфигурационном языке.

    Args:
        text: исходный текст конфигурации.

    Returns:
        Синтаксическое дерево lark.

    Raises:
        ConfigSyntaxError: если текст не соответствует грамматике.
    """
    try:
        return _PARSER.parse(text)
    except UnexpectedToken as err:
        raise _token_error(err) from err
    except UnexpectedCharacters as err:
        raise _char_error(err) from err
    except UnexpectedInput as err:
        raise ConfigSyntaxError(str(err), 0, 0) from err
