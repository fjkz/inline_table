#!/usr/bin/env python
from __future__ import print_function
import doctest
import sys
import unittest

import inline_table


class TestCompile(unittest.TestCase):

    def test_operator(self):
        tb = inline_table.compile_table("""
        === === ========
         a   b   aplusb
        === === ========
         1   1   1 + 1
        === === ========
        """)
        ret = tb.get_with_labels(a=1, b=1)["aplusb"]
        self.assertEqual(ret, 2)

    def test_variable(self):
        tb = inline_table.compile_table("""
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
        tb = inline_table.compile_table("""
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
            inline_table.compile_table("""
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
            inline_table.compile_table("""
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
        tb = inline_table.compile_table("""
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
        tb = inline_table.compile_table("""
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
        tb = inline_table.compile_table("""
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
        tb = inline_table.Table(['keyA', 'keyB', 'keyC'])
        ret = tb.labels
        self.assertEqual(ret, ['keyA', 'keyB', 'keyC'])

    def test_one_key_no_value(self):
        tb = inline_table.Table(['key'])
        try:
            tb.get(key='value')
            self.fail()
        except LookupError as _ok:
            pass

    def test_one_key_one_value(self):
        tb = inline_table.Table(['key'])
        tb._add(['value'])

        ret = tb.get(key='value')

        self.assertEqual(ret, ['value'])

    def test_one_key_two_value(self):
        tb = inline_table.Table(['key'])
        tb._add(['value1'])
        tb._add(['value2'])

        ret = tb.get(key='value1')

        self.assertEqual(ret, ['value1'])

    def test_two_key_two_value1(self):
        tb = inline_table.Table(['keyA', 'keyB'])
        tb._add(['value1A', 'value1B'])
        tb._add(['value2A', 'value2B'])

        ret = tb.get(keyA='value1A')

        self.assertEqual(ret, ['value1A', 'value1B'])

    def test_two_key_two_value2(self):
        tb = inline_table.Table(['keyA', 'keyB'])
        tb._add(['value1A', 'value1B'])
        tb._add(['value2A', 'value2B'])

        ret = tb.get(keyB='value2B')

        self.assertEqual(ret, ['value2A', 'value2B'])

    def test_get_with_labels(self):
        tb = inline_table.Table(['keyA', 'keyB'])
        tb._add(['value1A', 'value1B'])
        tb._add(['value2A', 'value2B'])

        ret = tb.get_with_labels(keyB='value2B')

        self.assertEqual(ret, {'keyA': 'value2A', 'keyB': 'value2B'})

    def test_incorrect_label(self):
        tb = inline_table.Table(['keyA', 'keyB'])
        try:
            tb.get(keyC=1)
            self.fail()
        except LookupError as _ok:
            pass


if __name__ == '__main__':
    result1 = doctest.testmod(inline_table)
    result2 = doctest.testfile('README.txt')
    attempted = result1.attempted + result2.attempted
    failed = result1.failed + result2.failed
    print('Ran %d tests' % attempted, file=sys.stderr)
    if failed > 0:
        sys.exit(1)
    else:
        print('OK', file=sys.stderr)
    unittest.main()
