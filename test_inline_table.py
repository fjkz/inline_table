from __future__ import print_function
import sys
import unittest

from docutils.parsers.rst.tableparser import SimpleTableParser
from docutils.statemachine import StringList
from inline_table import compile_table, Table, Parser


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


class TestParser(unittest.TestCase):

    def test_attrs1(self):
        ret = Parser().parse('''
        === ===
         a   b
        (A) (B)
        === ===
         1   2
        === ===
        ''')
        self.assertEqual(ret, (['a (A)', 'b (B)'], [['1', '2']]))

    def test_attrs2(self):
        ret = Parser().parse('''
        === ===
         a   b
        (A)
        === ===
         1   2
        === ===
        ''')
        self.assertEqual(ret, (['a (A)', 'b'], [['1', '2']]))

    def test_attrs3(self):
        ret = Parser().parse('''
        === ===
         a   b
            (B)
        === ===
         1   2
        === ===
        ''')
        self.assertEqual(ret, (['a', 'b (B)'], [['1', '2']]))

    def test_two_linebody(self):
        ret = Parser().parse('''
        === ===
         a   b
        === ===
         1   2
             3
        === ===
        ''')
        self.assertEqual(ret, (['a', 'b'], [['1', '2 3']]))


class TestCompile(unittest.TestCase):

    def test_operator(self):
        tb = compile_table("""
        === === ========
         a   b   aplusb
        === === ========
         1   1   1 + 1
        === === ========
        """)
        ret = tb.get_with_labels(a=1, b=1)["aplusb"]
        self.assertEqual(ret, 2)

    def test_variable(self):
        tb = compile_table("""
        === ===
         A   B
        === ===
         1   a
         2   b
        === ===
        """, a=1, b=2)

        ret = tb.get_with_labels(A=1)["B"]
        self.assertEqual(ret, 1)

        ret = tb.get_with_labels(A=2)["B"]
        self.assertEqual(ret, 2)

    def test_builtin(self):
        tb = compile_table("""
        ======
          A
        ======
        str(1)
        ======
        """)
        ret = tb.get(A='1')
        self.assertEqual(ret, ['1'])

    def test_variable_leak1(self):
        try:
            compile_table("""
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
            compile_table("""
            =====
             A
            =====
            table
            =====
            """)
            self.fail()
        except NameError as _ok:
            pass


class TestQuery(unittest.TestCase):

    def test_wildcard(self):
        tb = compile_table("""
        === ===
         A   B
        === ===
         1   1
         *   2
        === ===
        """)

        ret = tb.get(A=2)
        self.assertEqual(ret, [2, 2])
        # Assert WildCard is not included in the returned.
        self.assertEqual([str(v) for v in ret], ['2', '2'])

    def test_na(self):
        tb = compile_table("""
        === ===
         A   B
        === ===
         1  N/A
        === ===
        """)
        try:
            tb.get(A=1)
            self.fail()
        except LookupError as _ok:
            pass

    def test_na_for_key(self):
        tb = compile_table("""
        === ===
         A   B
        === ===
        N/A  1
         1   2
        === ===
        """)
        ret = tb.get(A=1)
        self.assertEqual(ret, [1, 2])


class TestTable(unittest.TestCase):

    def test_labels(self):
        tb = Table(['keyA', 'keyB', 'keyC'])
        ret = tb.labels
        self.assertEqual(ret, ['keyA', 'keyB', 'keyC'])

    def test_one_key_no_value(self):
        tb = Table(['key'])
        try:
            tb.get(key='value')
            self.fail()
        except LookupError as _ok:
            pass

    def test_one_key_one_value(self):
        tb = Table(['key'])
        tb._add(['value'])

        ret = tb.get(key='value')

        self.assertEqual(ret, ['value'])

    def test_one_key_two_value(self):
        tb = Table(['key'])
        tb._add(['value1'])
        tb._add(['value2'])

        ret = tb.get(key='value1')

        self.assertEqual(ret, ['value1'])

    def test_two_key_two_value1(self):
        tb = Table(['keyA', 'keyB'])
        tb._add(['value1A', 'value1B'])
        tb._add(['value2A', 'value2B'])

        ret = tb.get(keyA='value1A')

        self.assertEqual(ret, ['value1A', 'value1B'])

    def test_two_key_two_value2(self):
        tb = Table(['keyA', 'keyB'])
        tb._add(['value1A', 'value1B'])
        tb._add(['value2A', 'value2B'])

        ret = tb.get(keyB='value2B')

        self.assertEqual(ret, ['value2A', 'value2B'])

    def test_get_with_labels(self):
        tb = Table(['keyA', 'keyB'])
        tb._add(['value1A', 'value1B'])
        tb._add(['value2A', 'value2B'])

        ret = tb.get_with_labels(keyB='value2B')

        self.assertEqual(ret, {'keyA': 'value2A', 'keyB': 'value2B'})

    def test_incorrect_label(self):
        tb = Table(['keyA', 'keyB'])
        try:
            tb.get(keyC=1)
            self.fail()
        except LookupError as _ok:
            pass


class TestAttrubutes(unittest.TestCase):

    def test_oneline(self):
        tb = compile_table('''
            ==========
             a (value)
            ==========
             1
            ==========''')
        ret = tb.get(a=1)
        self.assertEqual(ret, [1])

    def test_value(self):
        tb = compile_table('''
            =========
             a
            (value)
            =========
             1
             2
            =========''')
        ret = tb.get(a=1)
        self.assertEqual(ret, [1])

    def test_condition(self):
        tb = compile_table('''
            =========== =====
             a           b
            (condition)
            =========== =====
            a < 0       True
            0 <= a      False
            =========== =====''')
        ret = tb.get(a=-1)
        self.assertEqual(ret, [-1, True])
        ret = tb.get(a=1)
        self.assertEqual(ret, [1, False])

    def test_condition_right(self):
        tb = compile_table('''
            ===== ===========
             a     b
                  (condition)
            ===== ===========
            True   b < 0
            False  b >= 0
            ===== ===========''')
        ret = tb.get(b=-1)
        self.assertEqual(ret, [True, -1])
        ret = tb.get(b=1)
        self.assertEqual(ret, [False, 1])

    def test_consition_wildcard(self):
        tb = compile_table('''
            =========== =====
             a           b
            (condition)
            =========== =====
            a < 0       True
            *           False
            =========== =====''')
        ret = tb.get(a=1)
        self.assertEqual(ret, [1, False])

    def test_consition_na(self):
        tb = compile_table('''
            =========== =====
             a           b
            (condition)
            =========== =====
            N/A         True
            0 <= a      False
            =========== =====''')
        ret = tb.get(a=1)
        self.assertEqual(ret, [1, False])

    def test_cond(self):
        tb = compile_table('''
            ====== ===
              A     B
            (cond)
            ====== ===
            A == 1  1
            A == 2  2
            ====== ===''')
        ret = tb.get(A=1)
        self.assertEqual(ret, [1, 1])

    def test_string(self):
        tb = compile_table('''
            ======== =====
            A        B
            (string) (str)
            ======== =====
            AAAAAAAA BBBBB
            aaaaaaaa bbbbb
            ======== =====''')
        ret = tb.get(A='AAAAAAAA')
        self.assertEqual(ret, ['AAAAAAAA', 'BBBBB'])

    def test_regex(self):
        tb = compile_table('''
            ======== =
             A       B
            (regex)
            ======== =
            r'^a+b$' 1
            r'b'     2
            N/A      3
            *        4
            ======== =''')
        ret1 = tb.get(A='aab')
        self.assertEqual(ret1, ['aab', 1])
        ret1 = tb.get(A='abb')
        self.assertEqual(ret1, ['abb', 4])


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
