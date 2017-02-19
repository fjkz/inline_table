from __future__ import print_function
import sys
import unittest

from docutils.parsers.rst.tableparser import SimpleTableParser
from docutils.statemachine import StringList
from inline_table import compile, Table, Format


class TestDocutils(unittest.TestCase):
    """Check the behavior of docutils."""

    def test_docutils1(self):
        text = '''\
=== ===
 a   b
=== ===
 1   2
=== ==='''
        ret = SimpleTableParser().parse(StringList(text.splitlines()))
        self.assertEqual(
            ret,
            (
                [3, 3],
                [
                    [[0, 0, 1, ['a']], [0, 0, 1, ['b']]]
                ],
                [
                    [[0, 0, 3, ['1']], [0, 0, 3, ['2']]]
                ]
            )
        )

    def test_docutils2(self):
        text = '''\
=== ===
 a   b
(A) (B)
=== ===
 1   2
=== ==='''
        ret = SimpleTableParser().parse(StringList(text.splitlines()))
        self.assertEqual(
            ret,
            (
                [3, 3],
                [
                    [[0, 0, 1, ['a']], [0, 0, 1, ['b']]],
                    [[0, 0, 2, ['(A)']], [0, 0, 2, ['(B)']]]
                ],
                [
                    [[0, 0, 4, ['1']], [0, 0, 4, ['2']]]
                ]
            )
        )

    def test_docutils3(self):
        text = '''\
=== ===
 a   b
(A)
=== ===
 1   2
=== ==='''
        ret = SimpleTableParser().parse(StringList(text.splitlines()))
        self.assertEqual(
            ret,
            (
                [3, 3],
                [
                    [[0, 0, 1, ['a']], [0, 0, 1, ['b']]],
                    [[0, 0, 2, ['(A)']], [0, 0, 2, ['']]]
                ],
                [
                    [[0, 0, 4, ['1']], [0, 0, 4, ['2']]]
                ]
            )
        )

    def test_docutils4(self):
        text = '''\
=== ===
 a   b
    (B)
=== ===
 1   2
=== ==='''
        ret = SimpleTableParser().parse(StringList(text.splitlines()))
        self.assertEqual(
            ret,
            (
                [3, 3],
                [
                    [[0, 0, 1, ['a', '']], [0, 0, 1, [' b', '(B)']]]
                ],
                [
                    [[0, 0, 4, ['1']], [0, 0, 4, ['2']]]
                ]
            )
        )

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
        ret = SimpleTableParser().parse(StringList(text.splitlines()))
        self.assertEqual(
            ret,
            (
                [3, 3, 3],
                [
                    [[0, 0, 1, ['a']], [0, 0, 1, ['b']], [0, 0, 1, ['c']]],
                    [[0, 0, 2, ['(A)']], [0, 0, 2, ['']], [0, 0, 2, ['']]]
                ],
                [
                    [[0, 0, 4, ['1']], [0, 0, 4, ['2']], [0, 0, 4, ['3']]]
                ]
            )
        )

    def test_docutils6(self):
        text = '''\
=== === ===
 a   b   c
    (B)
=== === ===
 1   2   3
=== === ==='''
        ret = SimpleTableParser().parse(StringList(text.splitlines()))
        self.assertEqual(
            ret,
            (
                [3, 3, 3],
                [
                    [[0, 0, 1, ['a', '']], [0, 0, 1, [' b', '(B)']],
                     [0, 0, 1, ['c', '']]]
                ],
                [
                    [[0, 0, 4, ['1']], [0, 0, 4, ['2']], [0, 0, 4, ['3']]]
                ]
            )
        )

    def test_docutils7(self):
        text = '''\
=== === ===
 a   b   c
        (C)
=== === ===
 1   2   3
=== === ==='''
        ret = SimpleTableParser().parse(StringList(text.splitlines()))
        self.assertEqual(
            ret,
            (
                [3, 3, 3],
                [
                    [[0, 0, 1, ['a', '']], [0, 0, 1, ['b', '']],
                     [0, 0, 1, [' c', '(C)']]]
                ],
                [
                    [[0, 0, 4, ['1']], [0, 0, 4, ['2']], [0, 0, 4, ['3']]]
                ]
            )
        )

    def test_docutils8(self):
        text = '''\
=== ===
 a   b
=== ===
 1   2
     3
=== ==='''
        ret = SimpleTableParser().parse(StringList(text.splitlines()))
        self.assertEqual(
            ret,
            (
                [3, 3],
                [
                    [[0, 0, 1, ['a']], [0, 0, 1, ['b']]]
                ],
                [
                    [[0, 0, 3, ['1', '']], [0, 0, 3, ['2', '3']]]
                ]
            )
        )


class TestFormatEstimation(unittest.TestCase):

    def test_simple_table1(self):
        fmt = Format.estimate_format(['=== ===\n',
                                      '=== ===\n'])
        self.assertTrue(fmt is Format.REST_SIMPLE_TABLE)

    def test_simple_table2(self):
        fmt = Format.estimate_format(['==\n',
                                      '=='])
        self.assertTrue(fmt is Format.REST_SIMPLE_TABLE)

    def test_grid_table1(self):
        fmt = Format.estimate_format(['+---+---+\n',
                                      '+---+---+\n'])
        self.assertTrue(fmt is Format.REST_GRID_TABLE)

    def test_grid_table2(self):
        fmt = Format.estimate_format(['+--+\n',
                                      '+--+'])
        self.assertTrue(fmt is Format.REST_GRID_TABLE)

    def test_markdown1(self):
        fmt = Format.estimate_format(['| a | b |\n',
                                      '|---|---|\n',
                                      '| c | d |\n'])
        self.assertTrue(fmt is Format.MARKDOWN_TABLE)

    def test_markdown2(self):
        fmt = Format.estimate_format(['| a | b |\n',
                                      '| - | - |\n',
                                      '| c | d |\n'])
        self.assertTrue(fmt is Format.MARKDOWN_TABLE)

    def test_markdown3(self):
        fmt = Format.estimate_format(['| a | b |\n',
                                      '|:- | -:|\n',
                                      '| c | d |\n'])
        self.assertTrue(fmt is Format.MARKDOWN_TABLE)

    def test_markdown4(self):
        fmt = Format.estimate_format([' a | b \n',
                                      '---|---\n',
                                      ' c | d \n'])
        self.assertTrue(fmt is Format.MARKDOWN_TABLE)

    def test_markdown5(self):
        fmt = Format.estimate_format(['a | b | c \n',
                                      ':--- |:--- |: ---\n',
                                      'c | d | e \n'])
        self.assertTrue(fmt is Format.MARKDOWN_TABLE)


class TestSimpleTableParser(unittest.TestCase):

    parser = Format.REST_SIMPLE_TABLE

    def test_attrs1(self):
        ret = self.parser.parse('''\
=== ===
 a   b
(A) (B)
=== ===
 1   2
=== ==='''.splitlines())
        self.assertEqual(ret, (['a (A)', 'b (B)'], [['1', '2']]))

    def test_attrs2(self):
        ret = self.parser.parse('''\
=== ===
 a   b
(A)
=== ===
 1   2
=== ==='''.splitlines())
        self.assertEqual(ret, (['a (A)', 'b'], [['1', '2']]))

    def test_attrs3(self):
        ret = self.parser.parse('''\
=== ===
 a   b
    (B)
=== ===
 1   2
=== ==='''.splitlines())
        self.assertEqual(ret, (['a', 'b (B)'], [['1', '2']]))

    def test_two_linebody(self):
        ret = self.parser.parse('''\
=== ===
 a   b
=== ===
 1   2
     3
=== ==='''.splitlines())
        self.assertEqual(ret, (['a', 'b'], [['1', '2 3']]))


class TestGridTableParser(unittest.TestCase):

    parser = Format.REST_GRID_TABLE

    def test_attrs1(self):
        ret = self.parser.parse('''\
+---+---+
| a | b |
|(A)|(B)|
+===+===+
| 1 | 2 |
+---+---+'''.splitlines())
        self.assertEqual(ret, (['a (A)', 'b (B)'], [['1', '2']]))

    def test_attrs2(self):
        ret = self.parser.parse('''\
+---+---+
| a | b |
|(A)|   |
+===+===+
| 1 | 2 |
+---+---+'''.splitlines())
        self.assertEqual(ret, (['a (A)', 'b'], [['1', '2']]))

    def test_attrs3(self):
        ret = self.parser.parse('''\
+---+---+
| a | b |
|   |(B)|
+===+===+
| 1 | 2 |
+---+---+'''.splitlines())
        self.assertEqual(ret, (['a', 'b (B)'], [['1', '2']]))

    def test_two_linebody(self):
        ret = self.parser.parse('''\
+---+---+
| a | b |
+===+===+
| 1 | 2 |
|   | 3 |
+---+---+'''.splitlines())
        self.assertEqual(ret, (['a', 'b'], [['1', '2 3']]))


class TestMarkdownParser(unittest.TestCase):

    parser = Format.MARKDOWN_TABLE

    def test_not_pretty(self):
        ret = self.parser.parse('''\
A | B | C |
---|:---|---:
a | b | c
1 | 2 | 3
'''.splitlines())
        self.assertEqual(
            ret,
            (['A', 'B', 'C'], [['a', 'b', 'c'], ['1', '2', '3']]))

    def test_no_space(self):
        ret = self.parser.parse('''\
|A|B|
|-|-|
|1|2|
'''.splitlines())
        self.assertEqual(
            ret,
            (['A', 'B'], [['1', '2']]))


class TestCompile(unittest.TestCase):

    def test_compile_with_format(self):
        tb = compile('''
        +---+---+
        | a | b |
        +===+===+
        | 1 | a |
        +---+---+''', a=1)
        tb.select(a=1, b=1)

    def test_operator(self):
        tb = compile("""
        === === ========
         a   b   aplusb
        === === ========
         1   1   1 + 1
        === === ========
        """)
        ret = tb.select(a=1, b=1).aplusb
        self.assertEqual(ret, 2)

    def test_variable(self):
        tb = compile("""
        === ===
         A   B
        === ===
         1   a
         2   b
        === ===
        """, a=1, b=2)

        ret = tb.select(A=1).B
        self.assertEqual(ret, 1)

        ret = tb.select(A=2).B
        self.assertEqual(ret, 2)

    def test_builtin(self):
        tb = compile("""
        ======
          A
        ======
        str(1)
        ======
        """)
        ret = tb.select(A='1')
        self.assertEqual(list(ret), ['1'])

    def test_variable_leak1(self):
        try:
            compile("""
            ===
             A
            ===
            re
            ===
            """)
            self.fail()
        except NameError as _ok:
            pass

    def test_variable_leak2(self):
        try:
            compile("""
            =====
             A
            =====
            table
            =====
            """)
            self.fail()
        except NameError as _ok:
            pass

    def test_markdown1(self):
        t = compile('''
        | A | B | C | D |
        |---|---|---|---|
        | 1 | 2 | 3 | 4 |
        ''')
        ret = t.select(A=1)
        self.assertEqual(list(ret), [1, 2, 3, 4])

    def test_markdown2(self):
        t = compile('''
          A | B | C | D
         ---|---|---|---
          1 | 2 | 3 | 4
        ''')
        ret = t.select(A=1)
        self.assertEqual(list(ret), [1, 2, 3, 4])


class TestQuery(unittest.TestCase):

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
        self.assertEqual(list(ret), [2, 2])
        # Assert WildCard is not included in the returned.
        self.assertEqual([str(v) for v in ret], ['2', '2'])

    def test_na(self):
        tb = compile("""
        === ===
         A   B
        === ===
         1  N/A
        === ===
        """)
        try:
            tb.select(A=1)
            self.fail()
        except LookupError as _ok:
            pass

    def test_na_for_key(self):
        tb = compile("""
        === ===
         A   B
        === ===
        N/A  1
         1   2
        === ===
        """)
        ret = tb.select(A=1)
        self.assertEqual(list(ret), [1, 2])


class TestTable(unittest.TestCase):

    def test_labels(self):
        tb = Table(['keyA', 'keyB', 'keyC'])
        ret = tb._labels
        self.assertEqual(list(ret), ['keyA', 'keyB', 'keyC'])

    def test_one_key_no_value(self):
        tb = Table(['key'])
        try:
            tb.select(key='value')
            self.fail()
        except LookupError as _ok:
            pass

    def test_one_key_one_value(self):
        tb = Table(['key'])
        tb._insert(['value'])

        ret = tb.select(key='value')

        self.assertEqual(list(ret), ['value'])

    def test_one_key_two_value(self):
        tb = Table(['key'])
        tb._insert(['value1'])
        tb._insert(['value2'])

        ret = tb.select(key='value1')

        self.assertEqual(list(ret), ['value1'])

    def test_two_key_two_value1(self):
        tb = Table(['keyA', 'keyB'])
        tb._insert(['value1A', 'value1B'])
        tb._insert(['value2A', 'value2B'])

        ret = tb.select(keyA='value1A')

        self.assertEqual(list(ret), ['value1A', 'value1B'])

    def test_two_key_two_value2(self):
        tb = Table(['keyA', 'keyB'])
        tb._insert(['value1A', 'value1B'])
        tb._insert(['value2A', 'value2B'])

        ret = tb.select(keyB='value2B')

        self.assertEqual(list(ret), ['value2A', 'value2B'])

    def test_incorrect_label(self):
        tb = Table(['keyA', 'keyB'])
        try:
            tb.select(keyC=1)
            self.fail()
        except LookupError as _ok:
            pass


class TestAttrubutes(unittest.TestCase):

    def test_oneline(self):
        tb = compile('''
            ==========
             a (value)
            ==========
             1
            ==========''')
        ret = tb.select(a=1)
        self.assertEqual(list(ret), [1])

    def test_value(self):
        tb = compile('''
            =========
             a
            (value)
            =========
             1
             2
            =========''')
        ret = tb.select(a=1)
        self.assertEqual(list(ret), [1])

    def test_condition(self):
        tb = compile('''
            =========== =====
             a           b
            (condition)
            =========== =====
            a < 0       True
            0 <= a      False
            =========== =====''')
        ret = tb.select(a=-1)
        self.assertEqual(list(ret), [-1, True])
        ret = tb.select(a=1)
        self.assertEqual(list(ret), [1, False])

    def test_condition_right(self):
        tb = compile('''
            ===== ===========
             a     b
                  (condition)
            ===== ===========
            True   b < 0
            False  b >= 0
            ===== ===========''')
        ret = tb.select(b=-1)
        self.assertEqual(list(ret), [True, -1])
        ret = tb.select(b=1)
        self.assertEqual(list(ret), [False, 1])

    def test_consition_wildcard(self):
        tb = compile('''
            =========== =====
             a           b
            (condition)
            =========== =====
            a < 0       True
            *           False
            =========== =====''')
        ret = tb.select(a=1)
        self.assertEqual(list(ret), [1, False])

    def test_consition_na(self):
        tb = compile('''
            =========== =====
             a           b
            (condition)
            =========== =====
            N/A         True
            0 <= a      False
            =========== =====''')
        ret = tb.select(a=1)
        self.assertEqual(list(ret), [1, False])

    def test_cond(self):
        tb = compile('''
            ====== ===
              A     B
            (cond)
            ====== ===
            A == 1  1
            A == 2  2
            ====== ===''')
        ret = tb.select(A=1)
        self.assertEqual(list(ret), [1, 1])

    def test_string(self):
        tb = compile('''
            ======== =====
            A        B
            (string) (str)
            ======== =====
            AAAAAAAA BBBBB
            aaaaaaaa bbbbb
            ======== =====''')
        ret = tb.select(A='AAAAAAAA')
        self.assertEqual(list(ret), ['AAAAAAAA', 'BBBBB'])

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
        ret1 = tb.select(A='aab')
        self.assertEqual(list(ret1), ['aab', 1])
        ret2 = tb.select(A='abb')
        self.assertEqual(list(ret2), ['abb', 4])


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
        self.assertEqual(list(tb.next()), [1])
        self.assertEqual(list(tb.next()), [2])
        self.assertEqual(list(tb.next()), [4])
        try:
            tb.next()
            self.fail()
        except StopIteration as _ok:
            pass

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
            self.assertTrue(x * 2 == y)
        self.assertEqual(i, 2)
        for i, (x, y) in enumerate(iter(tb)):
            self.assertTrue(x * 2 == y)
        self.assertEqual(i, 2)

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
            self.assertTrue(x * 2 == y)
        self.assertEqual(i, 2)
        for i, (x, y) in enumerate(iter(tb)):
            self.assertTrue(x * 2 == y)
        self.assertEqual(i, 2)


if __name__ == '__main__':
    import doctest
    import inline_table
    result1 = doctest.testmod(inline_table)
    result2 = doctest.testfile('README.rst')
    attempted = result1.attempted + result2.attempted
    failed = result1.failed + result2.failed
    print('Ran %d tests' % attempted, file=sys.stderr)
    if failed > 0:
        sys.exit(1)
    else:
        print('OK', file=sys.stderr)
    unittest.main()
