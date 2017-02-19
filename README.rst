===============================================================================
    inline_table - Python module for embedding text tables into source-code
===============================================================================

**inline_table** is a Python module for embedding text tables into source-code.

Table is a good notation. It is simple and easy to read. We can see if we
concern about all cases MECE-ly or not. We create many tables as software
design works: decision tables, state transition tables, etc.

We cannot, however, write tables directly with programming languages. We
convert tables to source-code with if-statements manually. Manual operations
usually cause mistakes. And today readability of source-code becomes important.
When we read source-code, we must reconstruct design tables from source-code.
This work is ineffective.

We need a way to write tables in source-code. We should be able to write code
as a document. The ``inline_table`` module enables us to do it.

Write a simple logic more simply.

Usage
=====

Compile a table text with the ``compile`` function. The table text must be
formatted with one of the following formats:

* reStructuredText Simple Table,
* reStructuredText Grid Table,
* Markdown Table.

The ``compile`` function returns a ``Table`` object. ::

    >>> import inline_table
    >>> t1 = inline_table.compile('''
    ...     === === ====
    ...      A   B   AB
    ...     === === ====
    ...      1   1  '1'
    ...      1   2  '2'
    ...      2   1  '2'
    ...      2   2  '4'
    ...     === === ====
    ...     ''')

The literals in the table body are evaluated in the compilation. ``1`` is an
integer and ``'1'`` is a string.

Search values in the ``Table`` object with the ``select`` method. A named tuple of
the first matched row is returned. ::

    >>> t1.select(A=1, B=2)
    Tuple(A=1, B=2, AB='2')

Other methods for getting rows are defined. See the pydoc.

We can pass values to a table. ::

    >>> t2 = inline_table.compile('''
    ...     === =====
    ...     key value
    ...     === =====
    ...      1    a
    ...      2    b
    ...     === =====
    ...     ''',
    ...     a='A', b='B')
    >>> t2.select(key=1)
    Tuple(key=1, value='A')

The wild card and the not-applicable value are provided. We can write them
respectively with ``*`` and ``N/A``. The wild card matches any value, and a
row including N/A is never returned. ::

    >>> t3 = inline_table.compile('''
    ...     === ===
    ...      K   V
    ...     === ===
    ...      1  N/A
    ...      *   1
    ...     === ===
    ...     ''')
    >>> t3.select(K=2)
    Tuple(K=2, V=1)
    >>> t3.select(K=1)
    Traceback (most recent call last):
        ...
    LookupError: The result is not applicable. condition: {'K': 1}

We can specify a column type with adding a keyword to the header
row. Four column types in the following table are provided.

=========== ========================== ===============================
Column Type Keyword                    Evaluated as
=========== ========================== ===============================
Value       (value), (val), no keyword Python literal
Condition   (condition), (cond)        Conditional statement.
                                       Use the 1st letter of the label
String      (string), (str)            String. Not support * and N/A
Regex       (regex), (re)              Regular expression
=========== ========================== ===============================

An example. ::

    >>> t4 = inline_table.compile('''
    ...     ========= ============= ========== =========
    ...     V (value) C (condition) S (string) R (regex)
    ...     ========= ============= ========== =========
    ...         1         C < 0        abc     r'[0-9]+'
    ...         2         C >= 0        *      r'[a-z]+'
    ...     ========= ============= ========== =========
    ...     ''')
    >>> t4.select(C=-1, R='012')
    Tuple(V=1, C=-1, S='abc', R='012')
    >>> t4.select(C=1, R='abc')
    Tuple(V=2, C=1, S='*', R='abc')

Installation
============

Run the following command for installation: ::

    $ python setup.py install

Requirements
============

* Python 2.6, 2.7 or 3.X
* docutils package 0.13 or later

License
=======

This work is released under the MIT License, see ``LICENSE.txt`` for details.
