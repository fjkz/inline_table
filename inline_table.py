"""Library for embedding text tables in source-code.

**inline_table** is a Python module for embedding text tables in
source-code. We can write source-code just like a design document.

The following is a basic example. Compile an text table text with the
``compile`` function. And get a row data with the ``select`` method. ::

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
    >>> t.select(state='stop', event='accel')
    Tuple(state='stop', event='accel', next='run', action='move')

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

    The following formats are supported:

    * reStructuredText Simple Table,
    * reStructuredText Grid Table,
    * Markdown Table.

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
    column_types = ['' for _ in range(len(labels))]

    # Move '(...)' word from labels to column_types.
    # e.g.,
    # label = 'a', column_type = '(a)'  --> label = 'a', column_type = '(a)'
    # label = 'a(a)', column_type = ''  --> label = 'a', column_type = '(a)'
    pattern = re.compile(r'([a-zA-Z_]+[0-9_]*) *(\([a-zA-Z0-9_]*\))')
    for i, s in enumerate(labels):
        match = pattern.match(s)
        if match:
            labels[i], column_types[i] = match.group(1, 2)

    # Convert strings to ColumnType values
    column_types = [ColumnType.get_column_type(a) for a in column_types]
    table = Table(labels, column_types)
    for row in rows:
        # Evaluate the literal in each cell with given variables.
        row_evaluated = []
        for i, cell in enumerate(row):
            column_type = column_types[i]
            label = labels[i]
            eval_val = column_type.evaluate(cell, variables, label)
            row_evaluated.append(eval_val)
        table._insert(row_evaluated)
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

    # Remove indent.
    # Count whitespaces of 1st and 2nd row, and regard the smaller one is
    # the indent width. The reason to see the 2nd row is for the case of
    # Markdown table without side '|'s.
    indent0 = re.search(r'\S', lines[0]).start()  # 1st row
    indent1 = re.search(r'\S', lines[1]).start()  # 2nd row
    indent = min(indent0, indent1)
    lines = [line[indent:] for line in lines]

    return lines


class Table:
    """Table data structure."""

    def __init__(self, labels, column_types=None):
        """Initialize the object.

        :param labels: list of label names
        :param column_types: list of column types
        """
        # Create a type of named tuple.
        # We name the type name as 'Tuple'. Traditionally, the row of
        # relational database is called tuple and it has attributes.
        self.Tuple = collections.namedtuple('Tuple', labels)

        if not column_types:
            column_types = [ColumnType.Value() for _ in labels]
        self.column_types = self.Tuple(*column_types)
        self.rows = []

    def __str__(self):
        """Return Tab separated values."""
        lines = []
        lines.append('\t'.join(self._labels))
        lines.append('\t'.join([str(a) for a in self.column_types]))
        for row in self.rows:
            lines.append('\t'.join([repr(c) for c in row]))
        return '\n'.join(lines)

    @property
    def _labels(self):
        """Return labels."""
        return self.column_types._fields

    @property
    def _num_columns(self):
        """Return the number of columns."""
        return len(self.column_types)

    @property
    def _num_rows(self):
        """Return the number of rows."""
        return len(self.rows)

    def _insert(self, row_values):
        """Add row data.

        :param row_values: list of values in a row
        """
        self.rows.append(self.Tuple(*row_values))

    def __iter__(self):
        """Return a iterator object.

        A row that contains the not-applicable value is skipped.

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
            >>> i = iter(t)
            >>> next(i)
            Tuple(A=1, B=2)
            >>> next(i)
            Tuple(A=3, B=6)
            >>> next(i)
            Tuple(A=WildCard, B=0)
            >>> next(i)
            Traceback (most recent call last):
                ...
            StopIteration

        """
        # Almost as same as select_all()
        return self.__select(condition={}, raise_error=False)

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
            condition = values
        elif isinstance(values, list) or isinstance(values, tuple):
            if len(values) != self._num_columns:
                return False
            condition = {}
            for i in range(self._num_columns):
                label = self._labels[i]
                condition[label] = values[i]
        else:
            return False

        try:
            self.select(**condition)
            return True
        except LookupError:
            return False

    def select(self, **condition):
        """Return the first row that matches the condition.

        :param condition: pairs of a column label and its value
        :return: the matched row
        :rtype: Tuple (named tuple)
        :raise LookupError: no applicable row is found for the condition

        :Example:

            >>> t = compile('''
            ... === =====
            ... key value
            ... === =====
            ... 'A'   1
            ... 'B'   2
            ... === =====
            ... ''')
            >>> t.select(key='A')
            Tuple(key='A', value=1)

        """
        if len(condition) == 0:
            raise LookupError("The condition is empty")

        return next(self.__select(condition, raise_error=True))

    def select_all(self, **condition):
        """Return all rows that match the condition.

        :Example:

            >>> t = compile('''
            ... === =====
            ... key value
            ... === =====
            ... 'A'   1
            ... 'A'  N/A
            ... 'B'   2
            ...  *    3
            ... === =====
            ... ''')
            >>> t.select_all(key='A')
            [Tuple(key='A', value=1), Tuple(key='A', value=3)]

        :param condition: pairs of a column label and its value
        :return: list of matched rows
        """
        rows = []
        generator = self.__select(condition, raise_error=False)
        while True:
            try:
                rows.append(next(generator))
            except StopIteration:
                return rows

    def __select(self, condition, raise_error):
        """Return a generator to select."""
        def format_condition(condition):
            """Format condition value to 'key1=a, key2=b' style."""
            return ', '.join(
                [key + '=' + repr(value) for key, value in condition.items()])

        def match(row):
            """Return True if all values in the row match the condition."""
            for label, condition_value in condition.items():
                row_value = getattr(row, label)
                column_type = getattr(self.column_types, label)
                if not column_type.match(row_value, condition_value):
                    return False
            return True

        for row in self.rows:
            if not match(row):
                continue

            # If the row is N/A raise an error.
            if NotApplicable in row:
                if raise_error:
                    raise LookupError(
                        "The result for the condition is not applicable: " +
                        format_condition(condition))
                else:
                    continue

            # Overwrite with the values in the condition
            # for excepting the wild card.
            for label, value in condition.items():
                kv = {label: value}
                row = row._replace(**kv)
            yield row

        # If no row is matched
        if raise_error:
            raise LookupError(
                "No row is found for the condition: " +
                format_condition(condition))
        # stop iteration

    def union(self, other):
        """Concatenate two tables.

        Two tables must have the same width, the same labels and
        the same type columns.

        Tables can be concatenated also with ``+`` operator.

        :param table: table to be concat
        :return: concatenated table
        :raise TypeError: width, labels or columns types are different
        """
        if self._num_columns != other._num_columns:
            raise TypeError(
                "Width of the tables are different: %d != %d" % (
                    self._num_columns, other._num_columns))

        if self._labels != other._labels:
            raise TypeError(
                "Labels of the tables are different: %s != %s" % (
                    str(self._labels), str(other._labels)))

        if self.column_types != other.column_types:
            def format_column_types(column_types):
                return '(%s)' % ', '.join([str(t) for t in column_types])

            raise TypeError(
                "Column types of the tables are different: %s != %s" % (
                    format_column_types(self.column_types),
                    format_column_types(other.column_types)))

        new_table = copy.copy(self)
        for row in other.rows:
            new_table._insert(row)
        return new_table

    def __add__(self, other):
        """Concatenate two tables.

        This is a syntax sugar of the ``union`` method.
        """
        return self.union(other)

    def join(self, other):
        """Join two tables.

        Tables can be joned also with ``*`` operator.

        This operation behave like NATURAL INNER JOIN in SQL.

        :Example:

            >>> t1 = compile('''
            ... | A | B |
            ... |---|---|
            ... | 1 | 1 |
            ... | 2 | 2 |''')
            >>> t2 = compile('''
            ... | A (cond)   | C |
            ... |------------|---|
            ... | A % 2 == 0 | 0 |
            ... | A % 2 == 1 | 1 |''')
            >>> t3 = t1.join(t2)
            >>> t3.select_all()
            [Tuple(A=1, B=1, C=1), Tuple(A=2, B=2, C=0)]

        :pram other: table to be join
        :return: joined table
        """
        l_labels = list(self._labels)
        r_labels = list(other._labels)
        order = (l_labels + r_labels).index
        union_labels = sorted(set(l_labels) | set(r_labels), key=order)

        def get_ctypes(table):
            ctypes = []
            for label in union_labels:
                try:
                    ctype = getattr(table.column_types, label)
                except AttributeError:
                    ctype = ColumnType._NoneType()
                ctypes.append(ctype)
            return ctypes

        # labels               LABEL1 LABEL2 LABEL3 LABEL4 LABEL5 LABEL6
        # left column types    val    cond   str    regex  coll
        # left column types           regex  str    cond   value  coll
        #
        # --> Fill with NONE
        # left column types    val    cond   str    regex  coll   NONE
        # left column types    NONE   regex  str    cond   value  coll
        #
        # --> Take join (Info about regex, str or coll are ommited)
        # union column types   val    cond   val    cond   cond   cond
        l_ctypes = get_ctypes(self)
        r_ctypes = get_ctypes(other)
        union_ctypes = [l_ctypes[i].join(r_ctypes[i])
                        for i, _ in enumerate(union_labels)]

        def getvalue(row, label):
            try:
                return getattr(row, label)
            except AttributeError:
                # If the row does not have the label, return the wild card.
                return WildCard

        joined_table = Table(union_labels, union_ctypes)

        for l_row in self.rows:
            for r_row in other.rows:
                #        LABEL1    LABEL2    LABEL3
                # l_row  val1      val2
                # r_row            val3      val4
                #
                # --> Fill with WildCard (Universal Set)
                # l_row  val1      val2      WildCard
                # r_row  WildCard  val3      val4
                #
                # --> Take intersection for each cell
                # joined val1&     val2&     WildCard&
                #   row   WildCard  val3      val4
                #
                # --> If a cell is empty set (IntersectionNotFound) skip the
                #     row, else add to the joined table.
                joined_row = []
                for i, label in enumerate(union_labels):
                    l_value = getvalue(l_row, label)
                    r_value = getvalue(r_row, label)
                    try:
                        value = union_ctypes[i].evaluate(l_value, r_value)
                    except IntersectionNotFound:
                        break
                    joined_row.append(value)
                else:
                    joined_table._insert(joined_row)

        return joined_table

    def __mul__(self, other):
        """Join two tables.

        This is a syntax sugar of the ``join`` method.
        """
        return self.join(other)


class ColumnType:
    """Type objects for columns."""

    @classmethod
    def get_column_type(cls, directive):
        for type_cls in (cls.Value,
                         cls.Condition,
                         cls.String,
                         cls.Regex,
                         cls.Collection):
            if directive in type_cls.DIRECTIVES:
                return type_cls()
        raise TableMarkupError("Invalid directive '%s'" % directive)

    class _TypeBase:
        """Abstract class of all type types."""

        def __eq__(self, other):
            return self.DIRECTIVES == other.DIRECTIVES

    class _ValueBase(_TypeBase):
        """Abstract class of value type types."""

        @property
        def is_set(self):
            return False

        def join(self, other):
            if other.is_set:
                return ColumnType._ValueJoinSet(self, other)
            else:
                return ColumnType._ValueJoinValue(self, other)

        def match(self, a, b):
            return a == b

    class _SetBase(_TypeBase):
        """Abstract class of set type types."""

        @property
        def is_set(self):
            return True

        def join(self, other):
            if other.is_set:
                return ColumnType._SetJoinSet(self, other)
            else:
                return ColumnType._SetJoinValue(self, other)

        def match(self, a, b):
            assert False, 'Not Implemented'

    class Value(_ValueBase):
        """Raw values.

        This column type is default.
        """

        DIRECTIVES = ('(value)', '(val)', '')  # Empty string is here.

        def __str__(self):
            return 'value'

        def evaluate(self, expression, variables, label):
            """Evaluate a string in the table cell."""
            if expression == WildCard.DIRECTIVE:
                return WildCard
            if expression == NotApplicable.DIRECTIVE:
                return NotApplicable
            return eval(expression, variables)

    class Condition(_SetBase):
        """Conditions.

        Data in a condition column is converted to functions.
        """

        DIRECTIVES = ('(condition)', '(cond)')

        def __str__(self):
            return 'condition'

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

                >>> f = ColumnType.Condition().evaluate('v > 0', {}, 'value')
                >>> f(1)
                True
                >>> f(-1)
                False

            """
            if expression == WildCard.DIRECTIVE:
                return WildCard
            if expression == NotApplicable.DIRECTIVE:
                return NotApplicable

            # Use first letter as symbol
            s = label[0]
            statement = 'lambda %s: %s' % (s, expression)
            return eval(statement, variables)

        def match(self, a, b):
            return a(b)

    class String(_ValueBase):
        """Strings.

        Data in this type column is not evaluated as Python literals.

        The wild card and the non-applicable value is not used for this
        column type.
        """

        DIRECTIVES = ('(string)', '(str)')

        def __str__(self):
            return 'string'

        def evaluate(self, expression, variables, label):
            # No wild card and N/A
            return expression

    class Regex(_SetBase):
        """Regular expression.

        The wild card and the non-applicable value is not used for this
        column type.
        """

        DIRECTIVES = ('(regex)', '(re)')

        def __str__(self):
            return 'regex'

        def evaluate(self, expression, variables, label):
            if expression == WildCard.DIRECTIVE:
                return WildCard
            if expression == NotApplicable.DIRECTIVE:
                return NotApplicable

            # Evaluate as Python literals and compile as a regular expression.
            return re.compile(eval(expression, variables))

        def match(self, a, b):
            if a.match(b):
                return True
            else:
                return False

    class Collection(_SetBase):
        """Collection."""

        DIRECTIVES = '(collection), (coll)'

        def __str__(self):
            return 'collection'

        def evaluate(self, expression, variables, label):
            """Evaluate as a python literal except '*' and 'N/A'."""
            if expression == WildCard.DIRECTIVE:
                return WildCard
            if expression == NotApplicable.DIRECTIVE:
                return NotApplicable
            col = eval(expression, variables)
            if not col.__contains__:
                raise ValueError("'%s' is not a collection" % expression)
            return col

        def match(self, a, b):
            if b in a:
                return True
            else:
                return False

    #
    # Following classes are used in Table.join
    #

    class _NoneType(Value):

        def evaluate(self, expression, variables, label):
            assert False, 'Cannot call _NoneType.evaluate'

    class _ValueJoinValue(Value):

        def __init__(self, left_type, right_type):
            self.left_type = left_type
            self.right_type = right_type

        def evaluate(self, left_value, right_value):
            try:
                return WildCard.get_intercect(left_value, right_value)
            except IntersectionNotFound:
                pass

            if left_value is NotApplicable and right_value is NotApplicable:
                return NotApplicable

            if self.left_type.match(left_value, right_value):
                # left and right are equivalent
                return left_value

            raise IntersectionNotFound

    class _ValueJoinSet(Value):
        def __init__(self, left_type, right_type):
            self.left_type = left_type
            self.right_type = right_type

        def evaluate(self, left_value, right_value):
            try:
                return WildCard.get_intercect(left_value, right_value)
            except IntersectionNotFound:
                pass

            if left_value is NotApplicable and right_value is NotApplicable:
                return NotApplicable

            if self.right_type.match(right_value, left_value):
                return left_value

            raise IntersectionNotFound

    class _SetJoinValue(Value):
        def __init__(self, left_type, right_type):
            self.left_type = left_type
            self.right_type = right_type

        def evaluate(self, left_value, right_value):
            try:
                return WildCard.get_intercect(left_value, right_value)
            except IntersectionNotFound:
                pass

            if left_value is NotApplicable and right_value is NotApplicable:
                return NotApplicable

            if self.left_type.match(left_value, right_value):
                return right_value

            raise IntersectionNotFound

    class _SetJoinSet(Condition):
        def __init__(self, left_type, right_type):
            self.left_type = left_type
            self.right_type = right_type

        def evaluate(self, left_value, right_value):
            try:
                return WildCard.get_intercect(left_value, right_value)
            except IntersectionNotFound:
                pass

            if left_value is NotApplicable and right_value is NotApplicable:
                return NotApplicable

            return lambda x: (self.left_type.match(left_value, x) and
                              self.right_type.match(right_value, x))


class IntersectionNotFound(Exception):
    """Used for internal controls."""

    pass


class _WildCard:
    """An object that equals with any value.

    The wild card is represented with '*' in table texts.

    In the module this object is used from ``WildCard`` variable,
    do not create a object directly.
    """

    DIRECTIVE = '*'

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

    def __contains__(self, x):
        """Return True for any object."""
        return True

    def __str__(self):
        """Return '*'."""
        return self.DIRECTIVE

    def __repr__(self):
        """Return 'WildCard'."""
        return 'WildCard'

    @staticmethod
    def get_intercect(a, b):
        if a is WildCard and b is WildCard:
            return WildCard
        if a is WildCard:
            return b
        if b is WildCard:
            return a
        raise IntersectionNotFound


WildCard = _WildCard()
"""The WildCard object. This is unique in the module."""


class _NotApplicable:
    """The non-applicable value.

    The non-applicable value is represented with 'N/A' in table texts.

    The object does not equal with any value.

    In the module this object is used from ``NotApplicable`` variable,
    do not create a object directly.
    """

    DIRECTIVE = 'N/A'

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

    def __contains__(self, x):
        """Return False for any object."""
        return False

    def __str__(self):
        """Return 'N/A'."""
        return self.DIRECTIVE

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
        for fmt in (Format.REST_SIMPLE_TABLE,
                    Format.REST_GRID_TABLE,
                    Format.MARKDOWN_TABLE):
            if fmt.can_accept(lines):
                return fmt

        raise TableMarkupError('The table format is unknown.')

    class _ReSTTable:
        """Sckeleton implementation of reStructuredText tables.

        In this class common logic between _ReSTSimpleTable and _ReSTGridTable
        is written. Both of them use the docutils package.
        """

        @classmethod
        def can_accept(cls, lines, line_pattern):
            """Check if the first/last line match the pattern."""
            if len(lines) < 3:
                return False

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

    class _MarkdownTable:
        """Markdown Table."""

        def can_accept(self, lines):
            """Judge if the table is estimated to be this format."""
            if len(lines) < 3:
                return False
            elif re.match(r' *\|? *[-:]+[-| :]*\|? *$', lines[1]):
                return True
            else:
                return False

        @classmethod
        def __split_cell(cls, line):
            # Remove leading |
            line = re.sub(r'^ *\| *', '', line)
            # Remove trailing |
            line = re.sub(r' *\| *$', '', line)
            # Split at |
            cells = re.split(r' *\| *', line)
            # Strip
            cells = [cell.strip() for cell in cells]
            return cells

        def parse(self, lines):
            r"""Parse a Markdown table.

            :Example:

                >>> Format.MARKDOWN_TABLE.parse('''\
                ... |  A  |  B  |  C  |
                ... |-----|:--- | ---:|
                ... |  a  |  b  |  c  |
                ... |  1  |  2  |  3  |
                ... '''.splitlines())
                (['A', 'B', 'C'], [['a', 'b', 'c'], ['1', '2', '3']])

            """
            header = self.__split_cell(lines[0])
            body = [self.__split_cell(line) for line in lines[2:]]
            return header, body

    REST_SIMPLE_TABLE = _ReSTSimpleTable()
    REST_GRID_TABLE = _ReSTGridTable()
    MARKDOWN_TABLE = _MarkdownTable()


class TableMarkupError(Exception):
    """Exception about a table text format."""

    pass
