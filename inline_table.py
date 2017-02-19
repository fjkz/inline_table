"""Library for embedding ASCII tables in source-code.

**inline_table** is a Python module for embedding ASCII tables in
source-code. We can write source-code just like a design document.

The following is a basic example. Compile an ASCII table text with the
``compile`` function. And search data with the ``get`` method. ::

    >>> import inline_table
    >>> t = inline_table.compile('''
    ... ====== ======= ====== ======
    ... state  event    next  action
    ... ====== ======= ====== ======
    ... 'stop' 'accel' 'run'  'move'
    ... 'stop' 'brake' 'stop'  None
    ... 'run'  'accel' 'run'  'move'
    ... 'run'  'brake' 'stop'  None
    ... ====== ======= ====== ======
    ... ''')
    >>> t.get(state='stop', event='accel')
    Row(state='stop', event='accel', next='run', action='move')

"""

import collections
import copy
import re

from docutils.parsers.rst.tableparser \
    import SimpleTableParser as DocutilsSimpleTableParser
from docutils.parsers.rst.tableparser \
    import GridTableParser as DocutilsGridTableParser
from docutils.parsers.rst.tableparser \
    import TableMarkupError as DocutilsTableMarkupError
from docutils.statemachine import StringList

__docformat__ = 'reStructuredText'
__version__ = '0.0'

__all__ = ('compile', 'Table', 'TableMarkupError')


def compile(text, **variables):
    """Compile a table text to a Table object.

    The text must be formated with reStructuredText Simple Table
    or Grid Table.

    Values can be passed to the table with the ``variables`` keyword arguments.
    They are used when literals in the table are evaluated.

    :param text: a table text
    :param variables: values passed to the table
    :type text: string
    :return: a table object
    :rtype: Table
    :raise TableMarkupError: the text format is incorrect
    """
    lines = text.splitlines()
    lines = strip_lines(lines)
    fmt = Format.estimate_format(lines)
    labels, rows = fmt.parse(lines)
    attrs = ['' for _ in range(len(labels))]

    # Move '(...)' word from labels to attrs.
    # e.g.,
    # label = 'a', attr = '(a)'  --> label = 'a', attr = '(a)'
    # label = 'a(a)', attr = ''  --> label = 'a', attr = '(a)'
    pattern = re.compile(r'([a-zA-Z_]+[0-9_]*) *(\([a-zA-Z0-9_]*\))')
    for i, s in enumerate(labels):
        match = pattern.match(s)
        if match:
            labels[i], attrs[i] = match.group(1, 2)

    enum_attrs = [Attribute.get_attr(a) for a in attrs]
    table = Table(labels, enum_attrs)
    for row in rows:
        # Evaluate the literal in each cell with given variables.
        row_evaluated = []
        for i, cell in enumerate(row):
            attr = enum_attrs[i]
            label = labels[i]
            eval_val = attr.evaluate(cell, variables, label)
            row_evaluated.append(eval_val)
        table._add(row_evaluated)
    return table


def strip_lines(lines):
    """Remove leading/trailing white lines and indents."""
    # Remove leading white lines.
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
    indent = re.search(r'\S', lines[0]).start()
    lines = [line[indent:] for line in lines]

    return lines


class Table:
    """Table data structure."""

    def __init__(self, labels, attrs=None):
        """Initialize the object.

        :param labels: list of label names
        :param attrs: list of column attributes
        :type labels: list of strings
        :type attrs: list of Attribute. The default is VALUE.
        """
        self.labels = labels
        # Create a type of named tuple.
        # The type name Row is proper?
        self.namedtuple = collections.namedtuple('Row', labels)

        if attrs:
            assert len(labels) == len(attrs)
        else:
            attrs = [Attribute.VALUE for _ in range(len(labels))]
        self.attrs = attrs
        self.rows_values = []

        self.iter_count = -1

    def __str__(self):
        """Return Tab separated values."""
        lines = []
        lines.append('\t'.join(self.labels))
        lines.append('\t'.join([str(a) for a in self.attrs]))
        for row in self.rows_values:
            lines.append('\t'.join([repr(c) for c in row]))
        return '\n'.join(lines)

    def _num_columns(self):
        """Return the number of columns."""
        return len(self.labels)

    def _num_rows(self):
        """Return the number of rows."""
        return len(self.rows_values)

    def _add(self, row_values):
        """Add row data.

        :param row_values: list of values in cells
        """
        assert len(row_values) == len(self.labels)
        self.rows_values.append(row_values)

    def __getitem__(self, i):
        """Return the i-th row.

        If the index of a ``*`` row or a ``N/A`` row is assigned,
        LookupError is raised.

        :param i: index
        :return: values in the i-th row
        :rtype: named tuple
        :raise LookupError: the index of a ``*`` or ``N/A`` row is assigned

        :Example:

            >>> t = compile('''
            ... === ===
            ...  A   B
            ... === ===
            ...  1   1
            ...  2  N/A
            ... === ===''')
            >>> t[0]
            Row(A=1, B=1)
            >>> t[1]
            Traceback (most recent call last):
                ...
            LookupError: The 1-th row is not applicable.

        """
        row = self.rows_values[i]
        for val in row:
            if val is WildCard or val is NotApplicable:
                raise LookupError('The %d-th row is not applicable.' % i)
        return self.namedtuple(*row)

    def __iter__(self):
        """Return a iterator object."""
        table = copy.copy(self)
        table.iter_count = -1
        return table

    # The next method is for Python 2 and
    # the __next__ method is for Python 3.
    def next(self):
        """Return the next row.

        A row that contains the wild card or the not-applicable value is
        skipped.

        :return: the next row
        :rtype: Row (named tuple)
        :raise StopIteration: the iteration is stopped

        :Example:

            >>> t = compile('''
            ... === ===
            ...  A   B
            ... === ===
            ...  1   2
            ...  2  N/A
            ...  3   6
            ...  *   0
            ... === ===''')
            >>> t.next()
            Row(A=1, B=2)
            >>> t.next()
            Row(A=3, B=6)
            >>> t.next()
            Traceback (most recent call last):
                ...
            StopIteration

        """
        while True:
            self.iter_count += 1
            if self.iter_count >= self._num_rows():
                raise StopIteration
            try:
                return self[self.iter_count]
            except LookupError:
                continue

    def __next__(self):
        """Return the next row values.

        See ``next`` method.
        """
        return self.next()

    def __contains__(self, values):
        """Check if this table contains given values with in-statements.

        A row contain N/A returns False.

        :Example:

            >>> t = compile('''
            ... === ===
            ...  A   B
            ... === ===
            ...  1   2
            ... === ===''')
            >>> {'A': 1} in t
            True
            >>> {'A': 2} in t
            False
            >>> (1, 2) in t
            True
            >>> [1, 2] in t
            True

        """
        if isinstance(values, dict):
            query = values
        elif isinstance(values, list) or isinstance(values, tuple):
            if len(values) != self._num_columns():
                return False
            query = {}
            for i in range(self._num_columns()):
                query[self.labels[i]] = values[i]
        else:
            return False

        try:
            self.get(**query)
            return True
        except LookupError:
            return False

    def __call__(self, **query):
        """Called as a function.

        The behavior is as same as ``get`` method.

        :Example:

            >>> f = compile('''
            ... === ===
            ...  x   y
            ... === ===
            ...  0   1
            ...  *   0
            ... === ===''')
            >>> f(x=0)
            Row(x=0, y=1)

        """
        return self.get(**query)

    def get(self, **query):
        """Return the first row that matches the query.

        :param query: pairs of a column label and its value
        :return: the matched row
        :rtype: Row (named tuple)
        :raise LookupError: no applicable row is found for the query

        :Example:

            >>> t = compile('''
            ... === =====
            ... key value
            ... === =====
            ... 'A'   1
            ... 'B'   2
            ... === =====
            ... ''')
            >>> t.get(key='A')
            Row(key='A', value=1)

        """
        # Convert key to index
        queryByIndex = []
        for k, v in query.items():
            try:
                i = self.labels.index(k)
            except ValueError:
                raise LookupError("The label '%s' is incorrect" % k)
            queryByIndex.append((i, v))

        def _match(values):
            """Return True if all values match the query."""
            for i, w in queryByIndex:
                v = values[i]
                a = self.attrs[i]
                if not a.match(v, w):
                    return False
            return True

        for i, values in enumerate(self.rows_values):
            if not _match(values):
                continue
            # matched

            # If the row is N/A raise an error.
            if NotApplicable in values:
                raise LookupError(
                    "The result is not applicable: query = %s" % query)

            # Overwrite with the values in the query
            # for excepting the wild card.
            values = copy.copy(values)
            for j, v in queryByIndex:
                values[j] = v
            return self.namedtuple(*values)

        # If no row is matched
        raise LookupError("No row is found for the query: %s" % query)


class Attribute:
    """Enum of attributes for columns."""

    @classmethod
    def get_attr(cls, symbol):
        if symbol in cls.VALUE.ALT_SYMBOLS:
            return cls.VALUE
        if symbol in cls.CONDITION.ALT_SYMBOLS:
            return cls.CONDITION
        if symbol in cls.STRING.ALT_SYMBOLS:
            return cls.STRING
        if symbol in cls.REGEX.ALT_SYMBOLS:
            return cls.REGEX
        raise TableMarkupError("Unknown symbol '%s'" % symbol)

    class _Value:
        """Raw values.

        This attribute is default.
        """

        SYMBOL = '(value)'
        ALT_SYMBOLS = (SYMBOL, '(val)', '')  # Empty string is here.

        def __str__(self):
            return self.SYMBOL

        def evaluate(self, expression, variables, label):
            """Evaluate a string in the table cell."""
            if expression == WildCard.SYMBOL:
                return WildCard
            if expression == NotApplicable.SYMBOL:
                return NotApplicable
            return eval(expression, variables)

        def match(self, a, b):
            return a == b

    class _Condition:
        """Conditions.

        Data in a condition column is converted to functions.
        """

        SYMBOL = '(condition)'
        ALT_SYMBOLS = (SYMBOL, '(cond)')

        def __str__(self):
            return self.SYMBOL

        def evaluate(self, expression, variables, label):
            """Return a function that checks if a value matches.

            In the expression the variable must be written with the first
            letter of the label. If the label is 'key', the expression is such
            as 'k > 0'.

            :param expression: condition statement
            :param variable: name and value pairs
                             that is passed to the expression
            :param label: name of column
            :return: function that takes one argument and returns True/False

            :Example:

                >>> f = Attribute.CONDITION.evaluate('v > 0', {}, 'value')
                >>> f(1)
                True
                >>> f(-1)
                False

            """
            if expression == WildCard.SYMBOL:
                return WildCard
            if expression == NotApplicable.SYMBOL:
                return NotApplicable

            # Use first letter as symbol
            s = label[0]
            statement = 'lambda %s: %s' % (s, expression)
            return eval(statement, variables)

        def match(self, a, b):
            return a(b)

    class _String:
        """Strings.

        Data with this attribute is not evaluated as Python literals.

        The wild card and the non-applicable value is not used for this
        attribute.
        """

        SYMBOL = '(string)'
        ALT_SYMBOLS = (SYMBOL, '(str)')

        def __str__(self):
            return self.SYMBOL

        def evaluate(self, expression, variables, label):
            # No wild card and N/A
            return expression

        def match(self, a, b):
            return a == b

    class _Regex:
        """Regular expression.

        The wild card and the non-applicable value is not used for this
        attribute.
        """

        SYMBOL = '(regex)'
        ALT_SYMBOLS = (SYMBOL, '(re)')

        def __str__(self):
            return self.SYMBOL

        def evaluate(self, expression, variables, label):
            if expression == WildCard.SYMBOL:
                return WildCard
            if expression == NotApplicable.SYMBOL:
                return NotApplicable

            # Evaluate as Python literals and compile as a regular expression.
            return re.compile(eval(expression, variables))

        def match(self, a, b):
            if a.match(b):
                return True
            else:
                return False

    # Values
    VALUE = _Value()
    CONDITION = _Condition()
    STRING = _String()
    REGEX = _Regex()


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

    def __call__(self, x):
        """Return True for called as a function."""
        return True

    def match(self, s):
        """Return True for called as a regex object."""
        return True

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

    def __call__(self, x):
        """Return False for called as a function."""
        return False

    def match(self, s):
        """Return False for called as a regex object."""
        return False

    def __str__(self):
        """Return 'N/A'."""
        return self.SYMBOL

    def __repr__(self):
        """Return 'NotApplicable'."""
        return 'NotApplicable'


NotApplicable = _NotApplicable()
"""The NotApplicable object. This is unique in the module."""


class Format:
    """Format of text tables."""

    @classmethod
    def estimate_format(cls, lines):
        """Estimate the format of the table text.

        The lines should be removed leading/trailing white lines and indents.
        Use strip_lines function.

        :pram lines: lines of the table text
        :return: estimated table format
        """
        if Format.REST_SIMPLE_TABLE.can_accept(lines):
            return Format.REST_SIMPLE_TABLE
        if Format.REST_GRID_TABLE.can_accept(lines):
            return Format.REST_GRID_TABLE
        raise TableMarkupError('The table format is unknown.')

    class _ReSTTable:
        """Sckeleton implementation of reStructuredText tables.

        In this class common logic between _ReSTSimpleTable and _ReSTGridTable
        is written. Both of them use the docutils package.
        """

        @classmethod
        def can_accept(cls, lines, line_pattern):
            """Check if the first/last line match the pattern."""
            first_line = lines[0]
            last_line = lines[-1]

            if (re.match(line_pattern, first_line) and
                    re.match(line_pattern, last_line)):
                return True
            else:
                return False

        @classmethod
        def parse(cls, lines, parser):
            """Parse a text table."""
            # See the document of the docutils module and my experiments in
            # test_inline_table.py for the data structure of the below result.
            try:
                data = parser.parse(StringList(lines))
            except DocutilsTableMarkupError as e:
                raise TableMarkupError(e)

            # === ===
            #  a   b   <- these
            #  c   d
            # === ===
            #  e   f
            # === ===
            labels = [' '.join(c[3]).strip() for c in data[1][0]]

            if len(data[1]) >= 2:
                # === ===
                #  a   b
                #  c   d   <- these
                # === ===
                #  e   f
                # === ===
                for row in data[1][1:]:
                    for i, cell in enumerate(row):
                        labels[i] += ' ' + ' '.join(cell[3])
                labels = [s.strip() for s in labels]

            # === ===
            #  a   b
            # === ===
            #  c   d   <- these
            #  e   f   <-
            # === ===
            rows = []
            for r in data[2]:
                rows.append([' '.join(c[3]).strip() for c in r])

            return labels, rows

    class _ReSTSimpleTable:
        """reStructuredText Simple Table."""

        def can_accept(self, lines):
            """Judge if the table is estimated to be this format."""
            return Format._ReSTTable.can_accept(lines, r'^ *[= ]*= *$')

        def parse(self, lines):
            r"""Parse reStructuredText SimpleTable.

            :param lines: lines of a table text
            :type text: string
            :return: tuple of list of labels and list of row values

            :Example:

                >>> Format.REST_SIMPLE_TABLE.parse('''\
                ... ==== ====
                ...  A    B
                ... ==== ====
                ...  a1   b1
                ...  a2   b2
                ... ==== ====
                ... '''.splitlines())
                (['A', 'B'], [['a1', 'b1'], ['a2', 'b2']])

                >>> Format.REST_SIMPLE_TABLE.parse('''\
                ... ==== ====
                ...  A    B
                ... (a)  (b)
                ... ==== ====
                ...  a1   b1
                ...  a2   b2
                ... ==== ====
                ... '''.splitlines())
                (['A (a)', 'B (b)'], [['a1', 'b1'], ['a2', 'b2']])

            """
            return Format._ReSTTable.parse(lines, DocutilsSimpleTableParser())

    class _ReSTGridTable:
        """reStructuredText Grid Table."""

        def can_accept(self, lines):
            """Judge if the table is estimated to be this format."""
            return Format._ReSTTable.can_accept(lines, r'^ *\+[-\+]*-\+ *$')

        def parse(self, lines):
            r"""Parse reStructuredText Grid Table.

            :Example:

                >>> Format.REST_GRID_TABLE.parse('''\
                ... +-----+-----+
                ... |  A  |  B  |
                ... | (a) | (b) |
                ... +=====+=====+
                ... | a1  | b1  |
                ... +-----+-----+
                ... | a2  | b2  |
                ... +-----+-----+
                ... '''.splitlines())
                (['A (a)', 'B (b)'], [['a1', 'b1'], ['a2', 'b2']])

            """
            return Format._ReSTTable.parse(lines, DocutilsGridTableParser())

    REST_SIMPLE_TABLE = _ReSTSimpleTable()
    REST_GRID_TABLE = _ReSTGridTable()


class TableMarkupError(Exception):
    """Exception about a table text format."""

    pass
