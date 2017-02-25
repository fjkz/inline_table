===================================================================================
                inline_table - Embedded text tables in Python code
===================================================================================

``inline_table`` is a Python module for embedding text tables into source-code.

The table is a good notation. It is simple and easy to read. We can see whether all
cases are taken into account or not. We create many tables as software design works:
decision tables, state transition tables, etc.

We cannot, however, write tables directly with programming languages. We manually
convert tables into source-code with if-statements. Manual operation often causes
mistakes. And today, the readability of source-code is important. When we read
source-code, we must reconstruct the design tables from the source-code. This work
is not effective.

We need a way to write tables in source-code. We should be able to write code as a
document. The ``inline_table`` module allows us to do this.

Let's write a simple logic more simply.

Example
=======

``inline_table`` compiles a text table to a ``Table`` object. We can query a
row in the table. The follow is an example: ::

    >>> import inline_table
    >>> text = '''
    ... ============ ======== ==========
    ... age (cond)   gender   call (str)
    ... ============ ======== ==========
    ...  0 <= a < 2   *       baby
    ...  0 <= a < 7   *       kid
    ...  7 <= a < 18  M       boy
    ...  7 <= a < 16  F       girl
    ... 18 <= a       M       gentleman
    ... 16 <= a       F       lady
    ...       *       *       man
    ... ============ ======== ==========
    ... '''
    >>> table = inline_table.compile(text, M='male', F='female')
    >>> table.select(age=24, gender='female')
    Tuple(age=24, gender='female', call='lady')

See the API document for the detail of the usage.

Installation
============

We can install the package with the following command: ::

    $ python setup.py install

Testing
=======

We can run unit-tests with the following command: ::

    $ python setup.py test

Requirements
============

* Python 2.6, 2.7, 3.2 or later
* docutils package 0.13 or later

License
=======

This work is released under the MIT License, see ``LICENSE.txt`` for details.
