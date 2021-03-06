===============================================================================
              inline_table - Embedded text tables in Python code
===============================================================================

``inline_table`` is a Python module for embedding text tables into source-code.

Table is a useful notation. It is simple and easy to read. We create many
tables as design works: decision tables, state transition tables, etc.

We cannot, however, write tables directly with programming languages. We
manually convert tables into code with if-statements. Manual operation often
causes mistakes. If-statements loss the readability. We need to reconstruct
tables when we read the source-code.

We should be able to write code as a document. The ``inline_table`` module
allows us to do this.

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
    ...  2 <= a < 7   *       kid
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

See `the API reference`_ for the detail of the usage.

.. _the API reference: https://fjkz.github.io/inline_table/0.1

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
