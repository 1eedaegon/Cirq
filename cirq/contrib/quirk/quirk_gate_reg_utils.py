# Copyright 2018 The Cirq Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import (
    Any,
    Callable,
    Union,
    Iterator,
)

import numpy as np
import sympy.parsing.sympy_parser

import cirq
from cirq.contrib.quirk.cells.cell import (CellMaker, CELL_SIZES,
    ExplicitOperationsCell,)


def parse_formula(formula: Any,
                  default_formula: Any = None) -> Union[float, sympy.Basic]:
    if formula is None:
        formula = default_formula
    if not isinstance(formula, str):
        raise TypeError('Formula must be a string: {!r}'.format(formula))

    formula = expand_unicode_fractions(formula)
    try:
        result = sympy.parsing.sympy_parser.parse_expr(formula)
    except SyntaxError as ex:
        raise SyntaxError(
            'Failed to parse the gate formula {!r}.\n'
            'This is likely due to differences in how sympy and Quirk parse.\n'
            'For example, Quirk allows "2 pi" whereas sympy requires "2*pi"\n'
            'Parsing of sympy-incompatible formulas is not supported yet.'
            ''.format(formula)) from ex
    if not result.free_symbols <= {sympy.Symbol('t')}:
        raise SyntaxError('Formula has variables besides time "t": {!r}'
                          ''.format(formula))
    if not result.free_symbols:
        result = float(result)
    return result


UNICODE_FRACTIONS = {
    "½": "(1/2)",
    "¼": "(1/4)",
    "¾": "(3/4)",
    "⅓": "(1/3)",
    "⅔": "(2/3)",
    "⅕": "(1/5)",
    "⅖": "(2/5)",
    "⅗": "(3/5)",
    "⅘": "(4/5)",
    "⅙": "(1/6)",
    "⅚": "(5/6)",
    "⅐": "(1/7)",
    "⅛": "(1/8)",
    "⅜": "(3/8)",
    "⅝": "(5/8)",
    "⅞": "(7/8)",
    "⅑": "(1/9)",
    "⅒": "(1/10)",
}


def expand_unicode_fractions(text: str) -> str:
    for k, v in UNICODE_FRACTIONS.items():
        text = text.replace('√' + k, f'(sqrt{v})')
        text = text.replace(k, v)
    return text


def parse_matrix(text: str) -> np.ndarray:
    if not text.startswith('{{') or not text.endswith('}}'):
        raise ValueError('No opening/closing braces.\ntext: {!r}'.format(text))
    text = expand_unicode_fractions(text[2:-2])
    rows = text.split('},{')
    return np.array([[_parse_complex(c) for c in row.split(',')] for row in rows
                    ])


def _parse_complex(text: str) -> complex:
    try:
        if (text.endswith('i') and len(text) > 1 and not text.endswith('+i') and
                not text.endswith('-i')):
            text = text[:-1] + '*i'
        expr = sympy.parsing.sympy_parser.parse_expr(text)
        return complex(expr.subs({'i': 1j}))
    except Exception as ex:
        raise ValueError(
            'Failed to parse complex from {!r}'.format(text)) from ex
