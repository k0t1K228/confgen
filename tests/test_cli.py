"""Тесты интерфейса командной строки."""

import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

from confgen.cli import EXIT_ERROR, EXIT_OK, main

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
USAGE_EXIT_CODE = 2


def run_cli(text: str, argv: list[str] | None = None):
    """Запускает main() с подставными потоками.

    Returns:
        Кортеж (код завершения, stdout, stderr).
    """
    stdout, stderr = io.StringIO(), io.StringIO()
    code = main(argv or [], io.StringIO(text), stdout, stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def test_success_writes_yaml_to_stdout():
    """Успешная трансляция пишет YAML в stdout, stderr пуст."""
    code, out, err = run_cli("let a = 2e0 begin x := ^[a * 3e0]; end")
    assert code == EXIT_OK
    assert out == "x: 6.0\n"
    assert not err


def test_all_constructs_together():
    """Все конструкции языка вместе, с вложенностью."""
    text = """
    * Конфигурация сервиса
    {{! Многострочный
        комментарий }}
    let base = 8e1
    let name = @"api"
    begin
      title := ^[name];
      ports := #(^[base], ^[base + 1e0], ^[min(base, 9e1)]);
      limits := begin
        cpu := ^[base / 2e0 - 1e1];
        tags := #(@"a", #(1e0, #()), begin k := 2e0; end);
      end;
    end
    """
    code, out, _ = run_cli(text)
    assert code == EXIT_OK
    assert out.splitlines() == [
        "title: api",
        "ports:",
        "- 80.0",
        "- 81.0",
        "- 80.0",
        "limits:",
        "  cpu: 30.0",
        "  tags:",
        "  - a",
        "  - - 1.0",
        "    - []",
        "  - k: 2.0",
    ]


def test_syntax_error_goes_to_stderr():
    """Синтаксическая ошибка: код 1, пустой stdout, сообщение в stderr."""
    code, out, err = run_cli("begin a := 1e0 end")
    assert code == EXIT_ERROR
    assert not out
    assert err.startswith("Синтаксическая ошибка: строка 1")


def test_evaluation_error_goes_to_stderr():
    """Ошибка вычисления: код 1, пустой stdout, сообщение в stderr."""
    code, out, err = run_cli("^[x]")
    assert code == EXIT_ERROR
    assert not out
    assert err.startswith("Ошибка вычисления:")
    assert "'x'" in err


def test_empty_input_is_error():
    """Пустой ввод не содержит значения и считается ошибкой."""
    code, out, err = run_cli("")
    assert code == EXIT_ERROR
    assert not out
    assert "конец ввода" in err


def test_help_exits_successfully(capsys):
    """Ключ --help печатает справку и завершает работу с кодом 0."""
    with pytest.raises(SystemExit) as info:
        main(["--help"])
    assert info.value.code == EXIT_OK
    output = capsys.readouterr().out
    assert "usage: confgen" in output
    assert "YAML" in output


def test_unknown_option_is_usage_error(capsys):
    """Неизвестный ключ даёт код 2 (ошибка использования)."""
    with pytest.raises(SystemExit) as info:
        main(["--unknown"])
    assert info.value.code == USAGE_EXIT_CODE
    assert capsys.readouterr().err


def test_real_process_stdin_to_stdout():
    """Запуск python -m confgen: stdin -> stdout, строки в UTF-8."""
    env = {**os.environ, "PYTHONPATH": str(SRC_DIR)}
    result = subprocess.run(
        [sys.executable, "-m", "confgen"],
        input='begin name := @"Привет"; end'.encode("utf-8"),
        capture_output=True,
        env=env,
        check=False,
    )
    assert result.returncode == EXIT_OK
    assert result.stdout.decode("utf-8") == "name: Привет\n"


def test_real_process_error_exit_code():
    """При ошибке процесс завершается с кодом 1 и пишет в stderr."""
    env = {**os.environ, "PYTHONPATH": str(SRC_DIR)}
    result = subprocess.run(
        [sys.executable, "-m", "confgen"],
        input=b"@",
        capture_output=True,
        env=env,
        check=False,
    )
    assert result.returncode == EXIT_ERROR
    assert not result.stdout
    assert "Синтаксическая ошибка" in result.stderr.decode("utf-8")
