"""Library for embedding ASCII tables in source-code.

**inline_table** is a Python module for embedding ASCII tables in source-code.
We can write source-code just like a design document.

The following is a basic example. Compile an ASCII table text with the
``compile_table`` function. And search data with the ``get`` method. ::

    >>> import inline_table
    >>> t = inline_table.compile_table('''
    ... ======= ======== ====== ======
    ... state   event    next   action
    ... ======= ======== ====== ======
    ... 'stop'  'accele' 'run'  'move'
    ... 'stop'  'brake'  'stop' None
    ... 'run'   'accele' 'run'  'move'
    ... 'run'   'brake'  'stop' None
    ... ======= ======== ====== ======
    ... ''')
    >>> t.get(state='stop', event='accele')
    ['stop', 'accele', 'run', 'move']

"""

from __future__ import print_function
import re

from docutils.parsers.rst.tableparser import (
    SimpleTableParser,
    TableMarkupError)
from docutils.statemachine import StringList

__docformat__ = 'reStructuredText'
__version__ = '0.0'

__all__ = ('compile_table', 'Table')


def compile_table(text, **variables):
    """Compile an ASCII table text to a Table object.

    The text must be formated with reStructuredText Simple Table.

    :param text: an ASCII table text
    :param variables: pairs of a name and value
                      used in evaluating literals in the text
    :type text: string
    :type variables: dict
    :return a table object
    :rtype Table
    :raise TableMarkupError: the text format is incorrect
    """
    def _evaluate(expression, variables):
        """Evaluate a string in the table cell."""
        if expression == WildCard.SYMBOL:
            return WildCard
        if expression == NotApplicable.SYMBOL:
            return NotApplicable
        else:
            return eval(expression, variables)

    labels, rows = Parser().parse(text)
    table = Table(labels)
    for row in rows:
        # Evaluate the literal in each cell with given variables.
        row_evaluated = [_evaluate(cell, variables) for cell in row]
        table._add(row_evaluated)
    return table


class Table:
    """Table data structure."""

    def __init__(self, labels):
        """Initialize the object.

        :param labels: list of label names
        :type labels: list of string
        """
        self.labels = labels
        self.rows = []

    def __str__(self):
        """Return Tab separated values."""
        lines = []
        lines.append('\t'.join(self.labels))
        for row in self.rows:
            lines.append('\t'.join([repr(c) for c in row]))
        return '\n'.join(lines)

    def _add(self, row):
        """Add row data.

        :param row: list of values.
                    Its length is equal to the number of labels.
        """
        assert len(row) == len(self.labels)
        self.rows.append(row)

    def get(self, **query):
        """Return the first row that matches with the query.

        :param query: pairs of a label name and value
        :type query: dict
        :return list of values
        :rtype list
        :raise LookupError: no applicable row is found for the query

        :Example:

        >>> t = compile_table('''
        ... === =====
        ... key value
        ... === =====
        ... 'A'   1
        ... 'B'   2
        ... === =====
        ... ''')
        >>> t.get(key='A')
        ['A', 1]

        """
        # Convert key to index
        queryByIndex = []
        for k, v in query.items():
            try:
                i = self.labels.index(k)
            except ValueError:
                raise LookupError("The label '%s' is incorrect" % k)
            queryByIndex.append((i, v))

        def _is_match(row):
            """Return True if the row matches with the query."""
            for i, v in queryByIndex:
                if row[i] != v:
                    return False
            return True

        for row in self.rows:
            if _is_match(row):
                # If the row is N/A raise an error.
                if NotApplicable in row:
                    raise LookupError(
                        "The result is not applicable: query = %s" % query)

                # Overwrite with the values in the query
                # for excepting the wild card.
                for i, v in queryByIndex:
                    row[i] = v
                return row

        # If no row is matched
        raise LookupError("No row is found for the query: %s" % query)

    def get_with_labels(self, **query):
        """Return the matched row with labels.

        :param query: pairs of a label name and value
        :type query: dict
        :return pairs of a label name and value
        :rtype dict
        :raise LookupError: no applicable row is found for the query

        :Example:

        >>> t = compile_table('''
        ... === =====
        ... key value
        ... === =====
        ... 'A'   1
        ... 'B'   2
        ... === =====
        ... ''')
        >>> r = t.get_with_labels(key='A')
        >>> r['key']
        'A'
        >>> r['value']
        1

        """
        r = {}
        result = self.get(**query)
        for i, v in enumerate(result):
            r[self.labels[i]] = v
        return r


class _WildCard:
    """An object that equals with any value.

    The wild card is represented in the ASCII table text with '*'.

    In the module this object is used from ``WildCard`` variable,
    do not create a object directly.
    """

    SYMBOL = '*'

    def __eq__(self, other):
        """Return True for any object."""
        return True

    def __ne__(self, other):
        """Return False for any object."""
        return False

    def __str__(self):
        """Return '*'."""
        return self.SYMBOL

    def __repr__(self):
        """Return 'WildCard'."""
        return 'WildCard'


WildCard = _WildCard()
"""The WildCard object. This is unique in the module."""


class _NotApplicable:
    """The non-applicable value.

    The non-applicable value is represented in the ASCII table text with 'N/A'.

    The object does not equal with any value.

    In the module this object is used from ``NotApplicable`` variable,
    do not create a object directly.
    """

    SYMBOL = 'N/A'

    def __eq__(self, other):
        """Return False for any object."""
        return False

    def __ne__(self, other):
        """Return True for any object."""
        return True

    def __str__(self):
        """Return 'N/A'."""
        return self.SYMBOL

    def __repr__(self):
        """Return 'NotApplicable'."""
        return 'NotApplicable'


NotApplicable = _NotApplicable()
"""The NotApplicable object. This is unique in the module."""


class Parser:
    """ASCII table parser.

    This class internally uses SimpleTableParser class in docutils module.
    """

    def parse(self, text):
        """Parse reStructured SimpleTable.

        :param text: ASCII table text
        :type text: string
        :return: list of labels, list of row values

        :Example:

        >>> Parser().parse('''
        ... ==== ====
        ...  A    B
        ... ==== ====
        ...  a1   b1
        ...  a2   b2
        ... ==== ====
        ... ''')
        (['A', 'B'], [['a1', 'b1'], ['a2', 'b2']])

        """
        lines = text.splitlines()

        # Remove leading while lines.
        while True:
            if re.match(r'^\s*$', lines[0]):
                del lines[0]
            else:
                break

        # Remove trailing white lines.
        while True:
            if re.match(r'^\s*$', lines[-1]):
                del lines[-1]
            else:
                break

        # Remove indent
        indent = lines[0].find('=')
        if indent < 0:
            raise TableMarkupError
        lines = [line[indent:] for line in lines]

        # See the document of the docutils module for the data
        # structure of the below result.
        data = SimpleTableParser().parse(StringList(lines))

        # === ===
        #  a   b   <- these
        #  c   d   <- ignored
        # === ===
        #  e   f
        # === ===
        labels = [c[3][0] for c in data[1][0]]

        # === ===
        #  a   b
        # === ===
        #  c   d   <- these
        #  e   f   <-
        # === ===
        rows = []
        for r in data[2]:
            rows.append([c[3][0] for c in r])

        return labels, rows
