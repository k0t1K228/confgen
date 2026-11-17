"""Вычисление констант и выражений на этапе трансляции."""

import copy
import math
import operator
from typing import Any

from lark import Token, Tree

from confgen.errors import ConfigEvalError

STRING_PREFIX_LEN = len('@"')
STRING_SUFFIX_LEN = len('"')


def _position(node: Tree | Token) -> tuple[int, int]:
    """Возвращает (строка, столбец) узла дерева или токена."""
    if isinstance(node, Token):
        return node.line, node.column
    return node.meta.line, node.meta.column


def _fail(node: Tree | Token, message: str) -> ConfigEvalError:
    """Создаёт ошибку вычисления с позицией узла."""
    line, column = _position(node)
    return ConfigEvalError(message, line, column)


def _divide(left: float, right: float) -> float:
    """Делит left на right (проверка нуля выполняется до вызова)."""
    return left / right


BINARY_OPERATIONS = {
    "add": operator.add,
    "sub": operator.sub,
    "mul": operator.mul,
    "div": _divide,
}


class Evaluator:
    """Вычисляет значение конфигурации по синтаксическому дереву."""

    def __init__(self) -> None:
        """Создаёт вычислитель с пустой таблицей констант."""
        self.constants: dict[str, Any] = {}

    def run(self, tree: Tree) -> Any:
        """Выполняет объявления let и возвращает итоговое значение."""
        *declarations, result = tree.children
        for declaration in declarations:
            self._declare(declaration)
        return self.value(result)

    def value(self, node: Tree) -> Any:
        """Вычисляет значение узла дерева."""
        handler = getattr(self, f"_eval_{node.data}")
        return handler(node)

    def _declare(self, node: Tree) -> None:
        """Объявляет константу: let имя = значение."""
        name_token, value_node = node.children
        name = str(name_token)
        if name in self.constants:
            raise _fail(name_token, f"константа '{name}' уже объявлена")
        self.constants[name] = self.value(value_node)

    def _eval_number(self, node: Tree) -> float:
        """Преобразует числовой литерал в float."""
        return float(node.children[0])

    def _eval_string(self, node: Tree) -> str:
        """Убирает обрамление @"..." у строки."""
        text = str(node.children[0])
        return text[STRING_PREFIX_LEN:-STRING_SUFFIX_LEN]

    def _eval_array(self, node: Tree) -> list[Any]:
        """Вычисляет элементы массива."""
        return [self.value(child) for child in node.children]

    def _eval_dict(self, node: Tree) -> dict[str, Any]:
        """Вычисляет словарь, запрещая повторяющиеся ключи."""
        result: dict[str, Any] = {}
        for entry in node.children:
            key_token, value_node = entry.children
            key = str(key_token)
            if key in result:
                raise _fail(key_token, f"повторяющийся ключ '{key}'")
            result[key] = self.value(value_node)
        return result

    def _eval_expr(self, node: Tree) -> Any:
        """Вычисляет константное выражение ^[...]."""
        return self.value(node.children[0])

    def _eval_var(self, node: Tree) -> Any:
        """Возвращает копию значения ранее объявленной константы."""
        token = node.children[0]
        name = str(token)
        if name not in self.constants:
            raise _fail(token, f"константа '{name}' не объявлена")
        return copy.deepcopy(self.constants[name])

    def _number(self, node: Tree) -> float:
        """Вычисляет узел и проверяет, что результат является числом."""
        result = self.value(node)
        if not isinstance(result, float):
            raise _fail(node, "операнд должен быть числом")
        return result

    def _binary(self, node: Tree) -> float:
        """Вычисляет бинарную операцию над двумя числами."""
        left_node, right_node = node.children
        left = self._number(left_node)
        right = self._number(right_node)
        if node.data == "div" and right == 0:
            raise _fail(right_node, "деление на ноль")
        result = BINARY_OPERATIONS[node.data](left, right)
        if not math.isfinite(result):
            raise _fail(node, "результат не является конечным числом")
        return result

    _eval_add = _binary
    _eval_sub = _binary
    _eval_mul = _binary
    _eval_div = _binary

    def _eval_call(self, node: Tree) -> float:
        """Вычисляет min() от одного или нескольких чисел."""
        return min(self._number(arg) for arg in node.children)


def evaluate(tree: Tree) -> Any:
    """Вычисляет итоговое значение конфигурации.

    Args:
        tree: дерево, полученное от confgen.parser.parse.

    Returns:
        Значение: float, str, list или dict (с вложенностью).

    Raises:
        ConfigEvalError: при неизвестной или повторной константе,
            повторном ключе словаря, неверном типе операнда,
            делении на ноль и переполнении.
    """
    return Evaluator().run(tree)
