from __future__ import print_function
import unittest
import doctest

from docutils.parsers.rst.tableparser import SimpleTableParser
from docutils.statemachine import StringList

import inline_table
from inline_table import *
from inline_table import Format, ColumnType, WILD_CARD, NOT_APPLICABLE


class TestDocutils(unittest.TestCase):
    """Check the behavior of docutils."""

    def assertParsedTo(self, text, expected):
        parsed = SimpleTableParser().parse(StringList(text.splitlines()))
        self.assertEqual(parsed, expected)

    def test_docutils1(self):
        text = '''\
=== ===
 a   b
=== ===
 1   2
=== ==='''
        expected = (
            [3, 3],
            [
                [[0, 0, 1, ['a']], [0, 0, 1, ['b']]]
            ],
            [
                [[0, 0, 3, ['1']], [0, 0, 3, ['2']]]
            ]
        )
        self.assertParsedTo(text, expected)

    def test_docutils2(self):
        text = '''\
=== ===
 a   b
(A) (B)
=== ===
 1   2
=== ==='''
        expected = (
            [3, 3],
            [
                [[0, 0, 1, ['a']], [0, 0, 1, ['b']]],
                [[0, 0, 2, ['(A)']], [0, 0, 2, ['(B)']]]
            ],
            [
                [[0, 0, 4, ['1']], [0, 0, 4, ['2']]]
            ]
        )
        self.assertParsedTo(text, expected)

    def test_docutils3(self):
        text = '''\
=== ===
 a   b
(A)
=== ===
 1   2
=== ==='''
        expected = (
            [3, 3],
            [
                [[0, 0, 1, ['a']], [0, 0, 1, ['b']]],
                [[0, 0, 2, ['(A)']], [0, 0, 2, ['']]]
            ],
            [
                [[0, 0, 4, ['1']], [0, 0, 4, ['2']]]
            ]
        )
        self.assertParsedTo(text, expected)

    def test_docutils4(self):
        text = '''\
=== ===
 a   b
    (B)
=== ===
 1   2
=== ==='''
        expected = (
            [3, 3],
            [
                [[0, 0, 1, ['a', '']], [0, 0, 1, [' b', '(B)']]]
            ],
            [
                [[0, 0, 4, ['1']], [0, 0, 4, ['2']]]
            ]
        )
        self.assertParsedTo(text, expected)

        # NOTE:
        # Position of '(B)' is different from other cases.
        # ' b' has a space at the first letter.

    def test_docutils5(self):
        text = '''\
=== === ===
 a   b   c
(A)
=== === ===
 1   2   3
=== === ==='''
        expected = (
            [3, 3, 3],
            [
                [[0, 0, 1, ['a']], [0, 0, 1, ['b']], [0, 0, 1, ['c']]],
                [[0, 0, 2, ['(A)']], [0, 0, 2, ['']], [0, 0, 2, ['']]]
            ],
            [
                [[0, 0, 4, ['1']], [0, 0, 4, ['2']], [0, 0, 4, ['3']]]
            ]
        )
        self.assertParsedTo(text, expected)

    def test_docutils6(self):
        text = '''\
=== === ===
 a   b   c
    (B)
=== === ===
 1   2   3
=== === ==='''
        expected = (
            [3, 3, 3],
            [
                [[0, 0, 1, ['a', '']], [0, 0, 1, [' b', '(B)']],
                 [0, 0, 1, ['c', '']]]
            ],
            [
                [[0, 0, 4, ['1']], [0, 0, 4, ['2']], [0, 0, 4, ['3']]]
            ]
        )
        self.assertParsedTo(text, expected)

    def test_docutils7(self):
        text = '''\
=== === ===
 a   b   c
        (C)
=== === ===
 1   2   3
=== === ==='''
        expected = (
            [3, 3, 3],
            [
                [[0, 0, 1, ['a', '']], [0, 0, 1, ['b', '']],
                 [0, 0, 1, [' c', '(C)']]]
            ],
            [
                [[0, 0, 4, ['1']], [0, 0, 4, ['2']], [0, 0, 4, ['3']]]
            ]
        )
        self.assertParsedTo(text, expected)

    def test_docutils8(self):
        text = '''\
=== ===
 a   b
=== ===
 1   2
     3
=== ==='''
        expected = (
            [3, 3],
            [
                [[0, 0, 1, ['a']], [0, 0, 1, ['b']]]
            ],
            [
                [[0, 0, 3, ['1', '']], [0, 0, 3, ['2', '3']]]
            ]
        )
        self.assertParsedTo(text, expected)


class TestFormatEstimation(unittest.TestCase):

    def assertEstimatedTo(self, lines, expected):
        fmt = Format.estimate_format(lines)
        self.assertTrue(fmt is expected)

    def test_simple_table1(self):
        self.assertEstimatedTo(
            ['=== ===\n'] * 3,
            Format.REST_SIMPLE_TABLE)

    def test_simple_table2(self):
        self.assertEstimatedTo(
            ['==\n'] * 3,
            Format.REST_SIMPLE_TABLE)

    def test_grid_table1(self):
        self.assertEstimatedTo(
            ['+---+---+\n',
             '+===+===+\n',
             '+---+---+\n'],
            Format.REST_GRID_TABLE)

    def test_grid_table2(self):
        self.assertEstimatedTo(
            ['+--+\n',
             '+==+\n',
             '+--+'],
            Format.REST_GRID_TABLE)

    def test_markdown1(self):
        self.assertEstimatedTo(
            ['| a | b |\n',
             '|---|---|\n',
             '| c | d |\n'],
            Format.MARKDOWN_TABLE)

    def test_markdown2(self):
        self.assertEstimatedTo(
            ['| a | b |\n',
             '| - | - |\n',
             '| c | d |\n'],
            Format.MARKDOWN_TABLE)

    def test_markdown3(self):
        self.assertEstimatedTo(
            ['| a | b |\n',
             '|:- | -:|\n',
             '| c | d |\n'],
            Format.MARKDOWN_TABLE)

    def test_markdown4(self):
        self.assertEstimatedTo(
            [' a | b \n',
             '---|---\n',
             ' c | d \n'],
            Format.MARKDOWN_TABLE)

    def test_markdown5(self):
        self.assertEstimatedTo(
            ['a | b | c \n',
             ':--- |:--- |: ---\n',
             'c | d | e \n'],
            Format.MARKDOWN_TABLE)

    def test_invalid_format1(self):
        self.assertRaises(TableMarkupError,
                          lambda: Format.estimate_format(['aaa']))

    def test_invalid_format2(self):
        self.assertRaises(TableMarkupError,
                          lambda: Format.estimate_format(['===']))


class TestSimpleTableParser(unittest.TestCase):

    def assertParsedTo(self, text, expected):
        parser = Format.REST_SIMPLE_TABLE
        ret = parser.parse(text.splitlines())
        self.assertEqual(ret, expected)

    def test_attrs1(self):
        text = '''\
=== ===
 a   b
(A) (B)
=== ===
 1   2
=== ==='''
        self.assertParsedTo(text, (['a (A)', 'b (B)'], [['1', '2']]))

    def test_attrs2(self):
        text = '''\
=== ===
 a   b
(A)
=== ===
 1   2
=== ==='''
        self.assertParsedTo(text, (['a (A)', 'b'], [['1', '2']]))

    def test_attrs3(self):
        text = '''\
=== ===
 a   b
    (B)
=== ===
 1   2
=== ==='''
        self.assertParsedTo(text, (['a', 'b (B)'], [['1', '2']]))

    def test_two_linebody(self):
        text = '''\
=== ===
 a   b
=== ===
 1   2
     3
=== ==='''
        self.assertParsedTo(text, (['a', 'b'], [['1', '2 3']]))


class TestGridTableParser(unittest.TestCase):

    def assertParsedTo(self, text, expected):
        parser = Format.REST_GRID_TABLE
        ret = parser.parse(text.splitlines())
        self.assertEqual(ret, expected)

    def test_attrs1(self):
        text = '''\
+---+---+
| a | b |
|(A)|(B)|
+===+===+
| 1 | 2 |
+---+---+'''
        self.assertParsedTo(text, (['a (A)', 'b (B)'], [['1', '2']]))

    def test_attrs2(self):
        text = '''\
+---+---+
| a | b |
|(A)|   |
+===+===+
| 1 | 2 |
+---+---+'''
        self.assertParsedTo(text, (['a (A)', 'b'], [['1', '2']]))

    def test_attrs3(self):
        text = '''\
+---+---+
| a | b |
|   |(B)|
+===+===+
| 1 | 2 |
+---+---+'''
        self.assertParsedTo(text, (['a', 'b (B)'], [['1', '2']]))

    def test_two_linebody(self):
        text = '''\
+---+---+
| a | b |
+===+===+
| 1 | 2 |
|   | 3 |
+---+---+'''
        self.assertParsedTo(text, (['a', 'b'], [['1', '2 3']]))


class TestMarkdownParser(unittest.TestCase):

    def assertParsedTo(self, text, expected):
        parser = Format.MARKDOWN_TABLE
        ret = parser.parse(text.splitlines())
        self.assertEqual(ret, expected)

    def test_not_pretty(self):
        text = '''\
A | B | C |
---|:---|---:
a | b | c
1 | 2 | 3
'''
        self.assertParsedTo(
            text,
            (['A', 'B', 'C'], [['a', 'b', 'c'], ['1', '2', '3']]))

    def test_no_space(self):
        text = '''\
|A|B|
|-|-|
|1|2|
'''
        self.assertParsedTo(
            text,
            (['A', 'B'], [['1', '2']]))


class TestCompile(unittest.TestCase):

    def test_operator(self):
        tb = compile("""
        === === ========
         a   b   aplusb
        === === ========
         1   1   1 + 1
        === === ========
        """)
        self.assertEqual(tb.select(a=1, b=1).aplusb, 2)

    def test_variable(self):
        tb = compile("""
        === ===
         A   B
        === ===
         1   a
         2   b
        === ===
        """, a=1, b=2)

        self.assertEqual(tb.select(A=1).B, 1)
        self.assertEqual(tb.select(A=2).B, 2)

    def test_builtin(self):
        tb = compile("""
        ======
          A
        ======
        str(1)
        ======
        """)
        self.assertEqual(tb.select(A='1'), ('1',))

    def test_variable_leak1(self):
        self.assertRaises(
            NameError,
            lambda: compile("""
                ===
                 A
                ===
                re
                ===
                """))

    def test_variable_leak2(self):
        self.assertRaises(
            NameError,
            lambda: compile("""
                =====
                 A
                =====
                table
                =====
                """))

    def test_grid_table(self):
        tb = compile('''
        +---+---+
        | a | b |
        +===+===+
        | 1 | a |
        +---+---+''', a=1)
        self.assertEqual(tb.select(a=1, b=1), (1, 1))

    def test_markdown1(self):
        t = compile('''
        | A | B | C | D |
        |---|---|---|---|
        | 1 | 2 | 3 | 4 |
        ''')
        self.assertEqual(t.select(A=1), (1, 2, 3, 4))

    def test_markdown2(self):
        t = compile('''
          A | B | C | D
         ---|---|---|---
          1 | 2 | 3 | 4
        ''')
        self.assertEqual(t.select(A=1), (1, 2, 3, 4))

    def test_invalid_directive(self):
        self.assertRaises(
            TableMarkupError,
            lambda: compile('''
                | A (foo) |
                |---------|
                | a       |
                '''))


class TestColumnType(unittest.TestCase):

    def test_oneline(self):
        tb = compile('''
            ==========
             a (value)
            ==========
             1
            ==========''')
        self.assertEqual(tb.select(a=1), (1,))

    def test_value(self):
        tb = compile('''
            =========
             a
            (value)
            =========
             1
             2
            =========''')
        self.assertEqual(tb.select(a=1), (1,))
        self.assertEqual(tb.select(a=2), (2,))

    def test_condition(self):
        tb = compile('''
            =========== =====
             a           b
            (condition)
            =========== =====
            a < 0       True
            0 <= a      False
            =========== =====''')
        self.assertEqual(tb.select(a=-1), (-1, True))
        self.assertEqual(tb.select(a=1), (1, False))

    def test_condition_right(self):
        tb = compile('''
            ===== ===========
             a     b
                  (condition)
            ===== ===========
            True   b < 0
            False  b >= 0
            ===== ===========''')
        self.assertEqual(tb.select(b=-1), (True, -1))
        self.assertEqual(tb.select(b=1), (False, 1))

    def test_consition_wildcard(self):
        tb = compile('''
            =========== =====
             a           b
            (condition)
            =========== =====
            a < 0       True
            *           False
            =========== =====''')
        self.assertEqual(tb.select(a=-1), (-1, True))
        self.assertEqual(tb.select(a=1), (1, False))

    def test_consition_na(self):
        tb = compile('''
            =========== =====
             a           b
            (condition)
            =========== =====
            N/A         True
            0 <= a      False
            =========== =====''')
        self.assertRaises(LookupError, lambda: tb.select(a=-1))
        self.assertEqual(tb.select(a=1), (1, False))

    def test_cond(self):
        tb = compile('''
            ====== ===
              A     B
            (cond)
            ====== ===
            A == 1  1
            A == 2  2
            ====== ===''')
        self.assertEqual(tb.select(A=1), (1, 1))
        self.assertEqual(tb.select(A=2), (2, 2))
        self.assertRaises(LookupError, lambda: tb.select(A=-1))

    def test_string(self):
        tb = compile('''
            ======== =====
            A        B
            (string) (str)
            ======== =====
            AAAAAAAA BBBBB
            aaaaaaaa bbbbb
            ======== =====''')
        self.assertEqual(tb.select(A='AAAAAAAA'), ('AAAAAAAA', 'BBBBB'))

    def test_regex(self):
        tb = compile('''
            ======== =
             A       B
            (regex)
            ======== =
            r'^a+b$' 1
            r'b'     2
            N/A      3
            *        4
            ======== =''')
        self.assertEqual(tb.select(A='aab'), ('aab', 1))
        self.assertEqual(tb.select(A='abb'), ('abb', 4))

    def test_collection(self):
        tb = compile('''
        | S(coll) | V |
        |---------|---|
        | 1, 2    | 1 |
        | N/A     | 2 |
        |  *      | 3 |''')
        self.assertEqual(tb.select(S=1), (1, 1))
        self.assertEqual(tb.select(S=2), (2, 1))
        self.assertEqual(tb.select(S=3), (3, 3))


class TestSelect(unittest.TestCase):

    def test_wildcard(self):
        tb = compile("""
        === ===
         A   B
        === ===
         1   1
         *   2
        === ===
        """)

        ret = tb.select(A=2)
        self.assertEqual(ret, (2, 2))
        self.assertTrue(ret[0] is not WILD_CARD)

    def test_na(self):
        tb = compile("""
        === ===
         A   B
        === ===
         1  N/A
        === ===
        """)
        self.assertRaises(LookupError, lambda: tb.select(A=1))

    def test_na_for_key(self):
        tb = compile("""
        === ===
         A   B
        === ===
        N/A  1
         1   2
        === ===
        """)
        self.assertEqual(tb.select(A=1), (1, 2))

    def test_no_arg(self):
        tb = compile("""
        === ===
         A   B
        === ===
         1   1
        === ===
        """)
        self.assertRaises(LookupError, lambda: tb.select())

    def test_invalid_label(self):
        tb = compile("""
        === ===
         A   B
        === ===
         1   1
        === ===
        """)
        try:
            tb.select(C=1)
            self.fail()
        except LookupError as ok:
            self.assertEqual(str(ok), "Label 'C' is invalid")


class TestSelectAll(unittest.TestCase):

    def test_no_matched(self):
        tb = compile("""
        === ===
         A   B
        === ===
         1   1
        === ===
        """)
        self.assertEqual(tb.select_all(A=2), [])

    def test_no_arg(self):
        tb = compile("""
        === ===
         A   B
        === ===
         1   1
         1   2
        === ===
        """)
        ret = tb.select_all()
        self.assertEqual(len(ret), 2)
        self.assertEqual(ret[0], (1, 1))
        self.assertEqual(ret[1], (1, 2))

    def test_invalid_label(self):
        tb = compile("""
        === ===
         A   B
        === ===
         1   1
        === ===
        """)
        try:
            tb.select_all(C=1)
            self.fail()
        except LookupError as ok:
            self.assertEqual(str(ok), "Label 'C' is invalid")


class TestTable(unittest.TestCase):

    def test_labels(self):
        tb = Table()._initialize(['keyA', 'keyB', 'keyC'])
        self.assertEqual(tb._labels, ('keyA', 'keyB', 'keyC'))

    def test_one_key_no_value(self):
        tb = Table()._initialize(['key'])
        self.assertRaises(LookupError, lambda: tb.select(key='value'))

    def test_one_key_one_value(self):
        tb = Table()._initialize(['key'])
        tb._insert(['value'])
        self.assertEqual(tb.select(key='value'), ('value',))

    def test_one_key_two_value(self):
        tb = Table()._initialize(['key'])
        tb._insert(['value1'])
        tb._insert(['value2'])
        self.assertEqual(tb.select(key='value1'), ('value1',))
        self.assertEqual(tb.select(key='value2'), ('value2',))

    def test_two_key_two_value1(self):
        tb = Table()._initialize(['keyA', 'keyB'])
        tb._insert(['value1A', 'value1B'])
        tb._insert(['value2A', 'value2B'])
        self.assertEqual(tb.select(keyA='value1A'), ('value1A', 'value1B'))
        self.assertEqual(tb.select(keyA='value2A'), ('value2A', 'value2B'))

    def test_two_key_two_value2(self):
        tb = Table()._initialize(['keyA', 'keyB'])
        tb._insert(['value1A', 'value1B'])
        tb._insert(['value2A', 'value2B'])
        self.assertEqual(tb.select(keyB='value1B'), ('value1A', 'value1B'))
        self.assertEqual(tb.select(keyB='value2B'), ('value2A', 'value2B'))


class TestUnion(unittest.TestCase):

    def test_union(self):
        t1 = compile('''
            | A | B |
            |---|---|
            | 1 | 2 |
            | 2 | 4 |''')
        t2 = compile('''
            | A | B |
            |---|---|
            | 3 | 6 |
            | 4 | 8 |''')
        t3 = t1.union(t2)
        it = iter(t3)
        self.assertEqual(next(it), (1, 2))
        self.assertEqual(next(it), (2, 4))
        self.assertEqual(next(it), (3, 6))
        self.assertEqual(next(it), (4, 8))

    def test_plus_operator(self):
        t1 = compile('''
            | A | B |
            |---|---|
            | 1 | 2 |
            | 2 | 4 |''')
        t2 = compile('''
            | A | B |
            |---|---|
            | 3 | 6 |
            | 4 | 8 |''')
        t3 = t1 + t2
        it = iter(t3)
        self.assertEqual(next(it), (1, 2))
        self.assertEqual(next(it), (2, 4))
        self.assertEqual(next(it), (3, 6))
        self.assertEqual(next(it), (4, 8))

    def test_width_diff(self):
        t1 = Table()._initialize(['a', 'b'])
        t2 = Table()._initialize(['a', 'b', 'c'])
        try:
            t1 + t2
            self.fail()
        except TypeError as e:
            self.assertEqual(
                str(e),
                "Width of the tables are different: 2 != 3")

    def test_labels_diff(self):
        t1 = Table()._initialize(['a', 'b'])
        t2 = Table()._initialize(['a', 'c'])
        try:
            t1 + t2
            self.fail()
        except TypeError as e:
            self.assertEqual(
                str(e),
                "Labels of the tables are different: ('a', 'b') != ('a', 'c')")

    def test_column_types_diff(self):
        t1 = Table()._initialize(
            ['a', 'b'],
            [ColumnType.Value(), ColumnType.Condition()])
        t2 = Table()._initialize(
            ['a', 'b'],
            [ColumnType.Value(), ColumnType.String()])
        try:
            t1 + t2
            self.fail()
        except TypeError as e:
            self.assertEqual(
                str(e),
                ('Column types of the tables are different: '
                 '(value, condition) != (value, string)'))


def assertIterationStop(iterator):
    try:
        next(iterator)
        assert False, 'Expect StopIteration is raised'
    except StopIteration:
        pass


class TestJoin(unittest.TestCase):

    def test_join_two_col(self):
        t1 = compile('''
        | A | B | C |
        |---|---|---|
        | 1 | 2 | 1 |
        | 1 | 1 | 2 |''')
        t2 = compile('''
        | A | B | D |
        |---|---|---|
        | 1 | 1 | 3 |
        | 1 | 1 | 4 |
        | 2 | 1 | 4 |''')
        t3 = t1 * t2
        self.assertEqual(t3._labels, ('A', 'B', 'C', 'D'))
        it = iter(t3)
        self.assertEqual(next(it), (1, 1, 2, 3))
        self.assertEqual(next(it), (1, 1, 2, 4))
        assertIterationStop(it)

    def test_join_zero_col(self):
        t1 = compile('''
        | A | B |
        |---|---|
        | 1 | 1 |
        | 2 | 2 |''')
        t2 = compile('''
        | C | D |
        |---|---|
        | 1 | 1 |
        | 2 | 2 |''')
        t3 = t1 * t2
        self.assertEqual(t3._labels, ('A', 'B', 'C', 'D'))
        it = iter(t3)
        self.assertEqual(next(it), (1, 1, 1, 1))
        self.assertEqual(next(it), (1, 1, 2, 2))
        self.assertEqual(next(it), (2, 2, 1, 1))
        self.assertEqual(next(it), (2, 2, 2, 2))
        assertIterationStop(it)

    def test_na(self):
        t1 = compile('''
        | A | B |
        |---|---|
        | 1 |N/A|
        | 2 | 1 |
        |N/A| 2 |
        | * | 3 |''')
        t2 = compile('''
        | A | C |
        |---|---|
        | 1 | 3 |
        | 2 |N/A|
        |N/A| 4 |
        | * | 5 |''')
        t3 = t1 * t2
        self.assertEqual(t3._labels, ('A', 'B', 'C'))
        self.assertEqual(t3._num_rows, 10)
        self.assertEqual(t3.rows[0], (1, NOT_APPLICABLE, 3))
        self.assertEqual(t3.rows[1], (1, NOT_APPLICABLE, 5))
        self.assertEqual(t3.rows[2], (2, 1, NOT_APPLICABLE))
        self.assertEqual(t3.rows[3], (2, 1, 5))
        self.assertEqual(t3.rows[4], (NOT_APPLICABLE, 2, 4))
        self.assertEqual(t3.rows[5], (NOT_APPLICABLE, 2, 5))
        self.assertEqual(t3.rows[6], (1,              3, 3))
        self.assertEqual(t3.rows[7], (2,              3, NOT_APPLICABLE))
        self.assertEqual(t3.rows[8], (NOT_APPLICABLE, 3, 4))
        self.assertEqual(t3.rows[9], (WILD_CARD,      3, 5))

    def test_wildcard_right(self):
        t1 = compile('''
        | A | B |
        |---|---|
        | 1 | 1 |
        | 2 | 2 |''')
        t2 = compile('''
        | A | C |
        |---|---|
        | 1 | 3 |
        | 2 | 4 |
        | * | 5 |''')
        t3 = t1 * t2
        self.assertEqual(t3._labels, ('A', 'B', 'C'))
        self.assertEqual(t3._num_rows, 4)
        it = iter(t3)
        self.assertEqual(next(it), (1, 1, 3))
        self.assertEqual(next(it), (1, 1, 5))
        self.assertEqual(next(it), (2, 2, 4))
        self.assertEqual(next(it), (2, 2, 5))
        assertIterationStop(it)

    def test_wildcard_left(self):
        t1 = compile('''
        | A | B |
        |---|---|
        | 1 | 1 |
        | 2 | 2 |
        | * | 3 |''')
        t2 = compile('''
        | A | C |
        |---|---|
        | 1 | 1 |
        | 2 | 2 |''')
        t3 = t1 * t2
        self.assertEqual(t3._labels, ('A', 'B', 'C'))
        self.assertEqual(t3._num_rows, 4)
        it = iter(t3)
        self.assertEqual(next(it), (1, 1, 1))
        self.assertEqual(next(it), (2, 2, 2))
        self.assertEqual(next(it), (1, 3, 1))
        self.assertEqual(next(it), (2, 3, 2))
        assertIterationStop(it)

    def test_condition_left(self):
        t1 = compile('''
        | A(cond) | B |
        |---------|---|
        | A < 0   | 1 |
        | A >= 0  | 2 |''')
        t2 = compile('''
        | A  | C |
        |----|---|
        | -1 | 1 |
        |  1 | 2 |''')
        t3 = t1 * t2
        self.assertEqual(t3._labels, ('A', 'B', 'C'))
        self.assertEqual(t3._num_rows, 2)
        it = iter(t3)
        self.assertEqual(next(it), (-1, 1, 1))
        self.assertEqual(next(it), (1, 2, 2))

    def test_condition_right(self):
        t1 = compile('''
        | A  | B |
        |----|---|
        | -1 | 1 |
        |  1 | 2 |''')
        t2 = compile('''
        | A(cond) | C |
        |---------|---|
        | A < 0   | 1 |
        | A >= 0  | 2 |''')
        t3 = t1 * t2
        self.assertEqual(t3._labels, ('A', 'B', 'C'))
        self.assertEqual(t3._num_rows, 2)
        it = iter(t3)
        self.assertEqual(next(it), (-1, 1, 1))
        self.assertEqual(next(it), (1, 2, 2))

    def test_condition_both(self):
        t1 = compile('''
        | A (cond) | B |
        |----------|---|
        | A > 0    | 0 |
        | *        | 1 |''')
        t2 = compile('''
        | A (cond) | C |
        |----------|---|
        | A < 2    | 0 |
        | *        | 1 |''')
        t3 = t1 * t2
        self.assertEqual(t3.select(A=-1), (-1, 1, 0))
        self.assertEqual(t3.select(A=1), (1, 0, 0))
        self.assertEqual(t3.select(A=3), (3, 0, 1))

    def test_collection_both(self):
        t1 = compile('''
        | A (coll) | B |
        |----------|---|
        | 1, 2, 3  | 0 |''')
        t2 = compile('''
        | A (coll) | C |
        |----------|---|
        | 2, 3, 4  | 1 |''')
        t3 = t1 * t2
        self.assertFalse((1, 0, 1) in t3)
        self.assertTrue((2, 0, 1) in t3)
        self.assertTrue((3, 0, 1) in t3)
        self.assertFalse((4, 0, 1) in t3)


class TestIterable(unittest.TestCase):

    def test_next(self):
        tb = compile('''
        ===
         x
        ===
         1
         2
        N/A
         4
         *
        ===''')
        it = iter(tb)
        self.assertEqual(next(it), (1,))
        self.assertEqual(next(it), (2,))
        self.assertEqual(next(it), (4,))
        self.assertTrue(next(it)[0] is WILD_CARD)
        assertIterationStop(it)

    def test_forloop1(self):
        tb = compile('''
        === ===
         x   y
        === ===
         1   2
         2   4
         3   6
         4  N/A
         *   0
        === ===''')
        for i, (x, y) in enumerate(tb):
            if x is WILD_CARD:
                self.assertEqual(y, 0)
            else:
                self.assertTrue(x * 2 == y)
        self.assertEqual(i, 3)
        for i, (x, y) in enumerate(tb):
            if x is WILD_CARD:
                self.assertEqual(y, 0)
            else:
                self.assertTrue(x * 2 == y)
        self.assertEqual(i, 3)

    def test_forloop2(self):
        tb = compile('''
        === ===
         x   y
        === ===
         1  N/A
         2   4
         3   6
         4   8
         *   0
        === ===''')
        for i, (x, y) in enumerate(tb):
            if x is WILD_CARD:
                self.assertEqual(y, 0)
            else:
                self.assertTrue(x * 2 == y)
        self.assertEqual(i, 3)


def suite():
    suite = unittest.TestSuite()
    suite.addTests([unittest.makeSuite(test_cls) for test_cls in (
        TestDocutils,
        TestFormatEstimation,
        TestSimpleTableParser,
        TestGridTableParser,
        TestMarkdownParser,
        TestCompile,
        TestSelect,
        TestSelectAll,
        TestTable,
        TestUnion,
        TestJoin,
        TestColumnType,
        TestIterable,
        )])
    suite.addTests(doctest.DocTestSuite(inline_table))
    suite.addTests(doctest.DocFileSuite('README.rst'))
    return suite
