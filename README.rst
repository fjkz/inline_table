===============================================================================
    inline_table - Python module for embedding ASCII tables in source-code
===============================================================================

**inline_table** is a Python module for embedding ASCII tables in source-code.

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

Compile an ASCII table text with the ``compile_table`` function. We can get a
`Table` object. We currently support only reStructuredText Simple Tables format.
::

    >>> import inline_table
    >>> t1 = inline_table.compile_table('''
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

Search values in the ``Table`` object with the ``get`` method. A list of values
in the first matched low is returned. ::

    >>> t1.get(A=1, B=2)
    [1, 2, '2']

We can pass variables to a table. ::

    >>> t2 = inline_table.compile_table('''
    ...     === =====
    ...     key value
    ...     === =====
    ...      1   a
    ...      2   b
    ...     === =====
    ...     ''',
    ...     a='A', b='B')
    >>> t2.get(key=1)
    [1, 'A']

The wild card and the not-applicable value are provided. We can write them
respectively with ``*`` and ``N/A``. The wild card matches with any query, and
a row including N/A is never returned. ::

    >>> t3 = inline_table.compile_table('''
    ...     === ===
    ...      K   V
    ...     === ===
    ...      1  N/A
    ...      *   1
    ...     === ===
    ...     ''')
    >>> t3.get(K=2)
    [2, 1]
    >>> t3.get(K=1)
    Traceback (most recent call last):
        ...
    LookupError: The result is not applicable: query = {'K': 1}

Installation
============

Run the following command for installation: ::

    $ python setup.py install

Requirements
============

* Python 2.6, 2.7 or 3.X
* docutils package 0.13.X

License
=======

This work is released under the MIT License, see ``LICENSE.txt`` for details.
