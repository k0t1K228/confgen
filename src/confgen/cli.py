"""Интерфейс командной строки: stdin -> YAML в stdout."""

import argparse
import sys
from typing import TextIO

from confgen.errors import ConfigError
from confgen.translator import translate

EXIT_OK = 0
EXIT_ERROR = 1

DESCRIPTION = (
    "Переводит учебный конфигурационный язык в YAML. "
    "Текст читается из стандартного ввода, результат пишется "
    "в стандартный вывод, ошибки выводятся в стандартный поток ошибок."
)


def build_arg_parser() -> argparse.ArgumentParser:
    """Создаёт разборщик аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="confgen",
        description=DESCRIPTION,
        add_help=False,
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="показать справку и выйти",
    )
    return parser


def _use_utf8(*streams: TextIO) -> None:
    """Переключает стандартные потоки на UTF-8, если это возможно."""
    for stream in streams:
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def main(
    argv: list[str] | None = None,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Запускает транслятор и возвращает код завершения.

    Args:
        argv: аргументы командной строки (по умолчанию sys.argv).
        stdin: поток ввода (по умолчанию sys.stdin).
        stdout: поток вывода (по умолчанию sys.stdout).
        stderr: поток ошибок (по умолчанию sys.stderr).

    Returns:
        0 при успехе, 1 при ошибке во входных данных.
    """
    build_arg_parser().parse_args(argv)
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    _use_utf8(stdin, stdout, stderr)
    try:
        result = translate(stdin.read())
    except ConfigError as err:
        print(f"{err.title}: {err}", file=stderr)
        return EXIT_ERROR
    except UnicodeDecodeError:
        print("Ошибка: входной текст должен быть в UTF-8", file=stderr)
        return EXIT_ERROR
    stdout.write(result)
    return EXIT_OK
