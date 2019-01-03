"""inline-table - Embedded text tables in Python code.

``inline_table`` is a Python module for embedding text tables into
source-code. We can write source-code just like a design document.
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
__version__ = '0.1.0'

__all__ = ('compile', 'Table', 'TableMarkupError')


def compile(text, **variables):
    """Compile a table text to a ``Table`` object.

    :param text: a table text
    :param variables: values passed to the table
    :type text: string
    :type variables: dict
    :return: a table object
    :rtype: Table
    :raise TableMarkupError: the text format is incorrect

    :Example:

        >>> text = '''
        ... ============ ======== ==========
        ...  age (cond)   gender  call (str)
        ... ============ ======== ==========
        ...       a < 0    N/A
        ...  0 <= a < 2     *     baby
        ...  0 <= a < 7     *     kid
        ...  7 <= a < 18    M     boy
        ...  7 <= a < 16    F     girl
        ... 18 <= a         M     gentleman
        ... 16 <= a         F     lady
        ...       *         *     man
        ... ============ ======== ==========
        ... '''
        >>> table = compile(text, M='male', F='female')
        >>> table.select(age=24, gender='female')
        Tuple(age=24, gender='female', call='lady')

    **Table Text Formats**:

    ``inline_table`` supports the following format as a table text:

    - `reStructuredText Simple Tables`_,
    - `reStructuredText Grid Tables`_,
    - `Markdown Tables`_.

    .. _reStructuredText Simple Tables: http://docutils.sourceforge.net/
                            docs/ref/rst/restructuredtext.html#simple-tables
    .. _reStructuredText Grid Tables: http://docutils.sourceforge.net/
                            docs/ref/rst/restructuredtext.html#grid-tables
    .. _Markdown Tables: https://michelf.ca/projects/php-markdown/extra/#table

    The format of the table text is estimated automatically.

    **Passing Values**:

    We can pass values to the table with the ``variables`` keyword arguments.
    Values can be passed with the following syntax: ::

        compile(text,
                <name>=<value>, <name>=<value>, ...)

    Here ``<name>`` are variable names written in the table text.

    **Special Values**:

    Two special values can be set to the table.

    ================ ========= ========================================
     Name            Directive Description
    ================ ========= ========================================
     Wild Card         ``*``   Matches any value. The universal set.
     Not-Applicable   ``N/A``  N/A rows are never returned for queries.
    ================ ========= ========================================

    If a string in a cell of the table text equals a directive, the cell is
    evaluated as the special value.

    Note that the string column type does not support the special values.

    **Column Types**:

    We can specify a column type with adding a directive to the header
    row. The difference among column types is how the strings in each cell are
    evaluated. ``inline_table`` provides five column types:

    =========== =============== =============================== ====
    Column Type Directive       Evaluated As                    Set?
    =========== =============== =============================== ====
    Value       No Directive,   Python literal                  no
                (value), (val)
    String      (string), (str) String.                         no
                                Not support ``*`` and ``N/A``.
    Condition   (condition),    Conditional statement.          yes
                (cond)          Use the 1st letter of the label
    Regex       (regex), (re)   Regular expression              yes
    Collection  (collection),   Collection of values            yes
                (coll)
    =========== =============== =============================== ====

    A cell in a set column type represents multiple values. The upper table and
    the lower table in the following act almost similarly (but not strictively
    equal). ::

        ========= ===
        a (coll)   b
        ========= ===
        (1, 2, 3)  4
        ========= ===

        ======= ===
        a (val)  b
        ======= ===
           1     4
           2     4
           3     4
        ======= ===

    """
    lines = strip_lines(text.splitlines())
    fmt = estimate_format(lines)
    labels, rows = fmt.parse(lines)
    coltype_strs = [''] * len(labels)

    # Move '(...)' word from labels to column_types.
    # e.g.,
    # label = 'a', column_type = '(a)'  --> label = 'a', column_type = '(a)'
    # label = 'a(a)', column_type = ''  --> label = 'a', column_type = '(a)'
    pattern = re.compile(r'([a-zA-Z_]+[0-9_]*) *(\([a-zA-Z0-9_]*\))')
    for i, label in enumerate(labels):
        match = pattern.match(label)
        if match:
            labels[i], coltype_strs[i] = match.group(1, 2)

    # Convert strings to ColumnType values
    column_types = [get_column_type(a) for a in coltype_strs]
    table = create_table(labels, column_types)
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
    lines = copy.copy(lines)

    def empty_line(line):
        """Return True if the line is white."""
        white_line_pattern = r'^\s*$'
        return re.match(white_line_pattern, line) is not None

    # Remove leading white lines.
    while True:
        if not lines:
            raise TableMarkupError('All lines are empty.')
        if not empty_line(lines[0]):
            break
        del lines[0]

    # Remove trailing white lines.
    while True:
        if not empty_line(lines[-1]):
            break
        del lines[-1]

    # Remove indent.
    # Count whitespaces of 1st and 2nd row, and regard the smaller one is
    # the indent width. The reason to see the 2nd row is for the case of
    # Markdown table without side '|'s.
    def first_char(line):
        """Return the position of first non-space character."""
        return re.search(r'\S', line).start()

    indent0 = first_char(lines[0])  # 1st row
    indent1 = first_char(lines[1])  # 2nd row
    indent = min(indent0, indent1)
    lines = [line[indent:] for line in lines]

    return lines


def create_table(labels, column_types=None):
    """Define a table schema and create a new table object.

    :param labels: list of label names
    :param column_types: list of column types
    """
    table = Table()
    # Create a type of named tuple.
    plaintuple_class = collections.namedtuple('PlainTuple', labels)

    # We name the type name as 'Tuple'. Traditionally, the row of
    # relational database is called tuple and it has attributes.
    class Tuple(plaintuple_class):
        """Row dataset."""

        def get(self, label, default=None):
            """Get the value on the labele."""
            try:
                return getattr(self, label)
            except AttributeError:
                if default is not None:
                    return default
                raise LookupError("Label '%s' is invalid" % label)

        def replace(self, **kwargs):
            """Return a new tuple replaced with given args."""
            # _replace is defined in tuple class.
            return self._replace(**kwargs)

        @classmethod
        def labels(cls):
            """Return label names of each column."""
            # _fields is defined in namedtuple().
            return cls._fields

    class ColumnTypeSet(Tuple):
        """Special tuple that contains the types of each field."""

        def __str__(self):
            """Return formatted string."""
            return '(%s)' % ', '.join([str(field) for field in self])

    table.tuple_class = Tuple
    table.types_class = ColumnTypeSet

    if column_types is None:
        column_types = [ValueType()] * len(labels)
    table.column_types = ColumnTypeSet(*column_types)

    return table


class Table:
    """Data structure having a table data.

    Table objects are created by the ``compile`` function.
    """

    def __init__(self):
        """Initialize this object."""
        self.tuple_class = None
        self.types_class = None
        self.column_types = None
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
        """Return label names of each column."""
        return self.tuple_class.labels()

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
        self.rows.append(self.tuple_class(*row_values))

    def iterator(self):
        """Return an iterator object.

        The ``iter`` build-in function and for-loops are also available.

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
            Tuple(A=WILD_CARD, B=0)
            >>> next(i)
            Traceback (most recent call last):
                ...
            StopIteration

        """
        # Almost as same as select_all()
        return self.__select(condition={}, raise_error=False)

    def __iter__(self):
        """Return self.iterator()."""
        return self.iterator()

    def contains(self, values):
        """Check if this table contains given values.

        In-statement is also available.

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
            >>> (1, 2) in t
            True

        """
        if isinstance(values, dict):
            condition = values
            try:
                self.select(**condition)
                return True
            except LookupError:
                return False

        elif isinstance(values, (list, tuple)):
            if len(values) != self._num_columns:
                return False
            condition = {}
            for i, label in enumerate(self._labels):
                condition[label] = values[i]
            return self.contains(condition)

        else:
            return False

    def __contains__(self, values):
        """Check if this table contains given values.

        This is a syntax suggar of the ``contains`` method.
        """
        return self.contains(values)

    def select(self, **condition):
        """Get the first row that matches the condition.

        :param condition: pairs of a column label and its value
        :return: the fist matched row
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
        if not condition:
            raise LookupError("The condition is empty")

        return next(self.__select(condition, raise_error=True))

    def select_all(self, **condition):
        """Get all rows that match the condition.

        :param condition: pairs of a column label and its value
        :return: list of matched rows
        :rtype: list of named tuples
        :raise LookupError: a key in the condition is invalid

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

        """
        row_generator = self.__select(condition, raise_error=False)
        return [row for row in row_generator]

    def __select(self, condition, raise_error):
        """Return a generator to select."""
        def format_condition(condition):
            """Format condition value to 'key1=a, key2=b' style."""
            return ', '.join(
                [key + '=' + repr(value) for key, value in condition.items()])

        def match(row):
            """Return True if all values in the row match the condition."""
            for label, condition_value in condition.items():
                row_value = row.get(label)
                column_type = self.column_types.get(label)
                if not column_type.match(row_value, condition_value):
                    return False
            return True

        def raise_error_if_allowed(message):
            """Raise LookupError if raise_error is True."""
            if raise_error:
                raise LookupError(message)

        for row in self.rows:
            if not match(row):
                continue

            # If the row is N/A raise an error.
            if NOT_APPLICABLE in row:
                raise_error_if_allowed(
                    "The result for the condition is not applicable: " +
                    format_condition(condition))
                continue

            # Overwrite with the values in the condition
            # for excepting the wild card.
            for label, value in condition.items():
                kv = {label: value}
                row = row.replace(**kv)
            yield row

        # If no row is matched
        raise_error_if_allowed(
            "No row is found for the condition: " +
            format_condition(condition))
        # stop iteration

    def union(self, other):
        """Concatenate two tables.

        Tables can be concatenated also with ``+`` operator.

        Two tables must have the same width, the same labels and
        the same type columns.

        :param other: a table to be concatenated
        :return: the concatenated table
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
            raise TypeError(
                "Column types of the tables are different: %s != %s" % (
                    str(self.column_types), str(other.column_types)))

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

        This method behaves like NATURAL INNER JOIN in SQL.

        :param other: a table to be join
        :return: the joined table

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
            >>> t3 = t1.join(t2)  # ``t1 * t2`` is equivalent
            >>> t3.select_all()
            [Tuple(A=1, B=1, C=1), Tuple(A=2, B=2, C=0)]

        """
        l_labels = list(self._labels)
        r_labels = list(other._labels)
        order = (l_labels + r_labels).index
        union_labels = sorted(set(l_labels) | set(r_labels), key=order)

        def get_ctypes(table):
            vtype = VirtualType()
            ctypes = [table.column_types.get(label, default=vtype)
                      for label in union_labels]
            return ctypes

        # labels               LABEL1 LABEL2 LABEL3 LABEL4 LABEL5 LABEL6
        # left column types    val    cond   str    regex  coll
        # left column types           regex  str    cond   value  coll
        #
        # --> Fill with Virtual
        # left column types    val    cond   str    regex  coll   Virt
        # left column types    Virt   regex  str    cond   value  coll
        #
        # --> Take join (Info about regex, str or coll are ommited)
        # union column types   val    cond   val    cond   cond   cond
        l_ctypes = get_ctypes(self)
        r_ctypes = get_ctypes(other)
        union_ctypes = [l_ctypes[i].join(r_ctypes[i])
                        for i, _ in enumerate(union_labels)]

        joined_table = create_table(union_labels, union_ctypes)

        for l_row in self.rows:
            for r_row in other.rows:
                #        LABEL1    LABEL2    LABEL3
                # l_row  val1      val2
                # r_row            val3      val4
                #
                # --> Fill with WILD_CARD (Universal Set)
                # l_row  val1      val2      WILD_CARD
                # r_row  WILD_CARD val3      val4
                #
                # --> Take intersection for each cell
                # joined val1&     val2&     WILD_CARD&
                #   row   WILD_CARD  val3     val4
                #
                # --> If a cell is empty set (IntersectionNotFound) skip the
                #     row, else add to the joined table.
                joined_row = []
                for i, label in enumerate(union_labels):
                    # If the row does not have the label, return the wild card.
                    l_value = l_row.get(label, default=WILD_CARD)
                    r_value = r_row.get(label, default=WILD_CARD)
                    try:
                        value = union_ctypes[i].join_values(l_value, r_value)
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


def get_column_type(directive):
    """Return a column type that matches the given directive."""
    for type_cls in (
            ValueType, ConditionType, StringType,
            RegexType, CollectionType):
        if directive in type_cls.directives:
            return type_cls()
    else:
        raise TableMarkupError("Invalid directive '%s'" % directive)


class ColumnTypeBase:
    """Abstract class of all type types."""

    directives = ()

    def __eq__(self, other):
        return self.directives == other.directives


class ValueTypeBase(ColumnTypeBase):
    """Abstract class of value type types."""

    is_set = False

    def join(self, other):
        if other.is_set:
            return ValueXSetType(self, other)
        else:
            return ValueXValueType(self, other)

    @staticmethod
    def match(a, b):
        return a == b


class SetTypeBase(ColumnTypeBase):
    """Abstract class of set type types."""

    is_set = True

    def join(self, other):
        if other.is_set:
            return SetXSetType(self, other)
        else:
            return SetXValueType(self, other)

    @staticmethod
    def match(a, b):
        assert False, 'Not Implemented'


class ValueType(ValueTypeBase):
    """Raw values.

    This column type is default.
    """

    # Empty string is here.
    directives = ('', '(value)', '(val)', '')

    def __str__(self):
        return 'value'

    @staticmethod
    def evaluate(expression, variables, label):
        """Evaluate a string in the table cell."""
        if expression == WILD_CARD.directive:
            return WILD_CARD
        if expression == NOT_APPLICABLE.directive:
            return NOT_APPLICABLE
        return eval(expression, variables)


class ConditionType(SetTypeBase):
    """Conditions.

    Data in a condition column is converted to functions.
    """

    directives = ('(condition)', '(cond)')

    def __str__(self):
        return 'condition'

    @staticmethod
    def evaluate(expression, variables, label):
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

            >>> f = ConditionType().evaluate('v > 0', {}, 'value')
            >>> f(1)
            True
            >>> f(-1)
            False

        """
        if expression == WILD_CARD.directive:
            return WILD_CARD
        if expression == NOT_APPLICABLE.directive:
            return NOT_APPLICABLE

        # Use first letter as symbol
        symbol = label[0]
        statement = 'lambda %s: %s' % (symbol, expression)
        return eval(statement, variables)

    @staticmethod
    def match(a, b):
        return a(b)


class StringType(ValueTypeBase):
    """Strings.

    Data in this type column is not evaluated as Python literals.

    The wild card and the non-applicable value is not used for this
    column type.
    """

    directives = ('(string)', '(str)')

    def __str__(self):
        return 'string'

    @staticmethod
    def evaluate(expression, variables, label):
        # No wild card and N/A
        return expression


class RegexType(SetTypeBase):
    """Regular expression.

    The wild card and the non-applicable value is not used for this
    column type.
    """

    directives = ('(regex)', '(re)')

    def __str__(self):
        return 'regex'

    @staticmethod
    def evaluate(expression, variables, label):
        if expression == WILD_CARD.directive:
            return WILD_CARD
        if expression == NOT_APPLICABLE.directive:
            return NOT_APPLICABLE

        # Evaluate as Python literals and compile as a regular expression.
        return re.compile(eval(expression, variables))

    @staticmethod
    def match(a, b):
        if a.match(b):
            return True
        return False


class CollectionType(SetTypeBase):
    """Collection."""

    directives = '(collection), (coll)'

    def __str__(self):
        return 'collection'

    @staticmethod
    def evaluate(expression, variables, label):
        """Evaluate as a python literal except '*' and 'N/A'."""
        if expression == WILD_CARD.directive:
            return WILD_CARD
        if expression == NOT_APPLICABLE.directive:
            return NOT_APPLICABLE
        col = eval(expression, variables)
        if not col.__contains__:
            raise ValueError("'%s' is not a collection" % expression)
        return col

    @staticmethod
    def match(a, b):
        if b in a:
            return True
        return False


#
# Following classes are used in Table.join
#
class VirtualType(ValueType):

    @staticmethod
    def evaluate(expression, variables, label):
        assert False, 'Cannot call Virtual.evaluate'


class ValueXValueType(ValueType):

    def __init__(self, left_type, right_type):
        self.left_type = left_type
        self.right_type = right_type

    def join_values(self, left_value, right_value):
        """Return intersection of two values."""
        try:
            return WILD_CARD.get_intercect(left_value, right_value)
        except IntersectionNotFound:
            pass

        if left_value is NOT_APPLICABLE and right_value is NOT_APPLICABLE:
            return NOT_APPLICABLE

        if self.left_type.match(left_value, right_value):
            # left and right are equivalent
            return left_value

        raise IntersectionNotFound


class ValueXSetType(ValueType):
    def __init__(self, left_type, right_type):
        self.left_type = left_type
        self.right_type = right_type

    def join_values(self, left_value, right_value):
        """Return intersection of two values."""
        try:
            return WILD_CARD.get_intercect(left_value, right_value)
        except IntersectionNotFound:
            pass

        if left_value is NOT_APPLICABLE and right_value is NOT_APPLICABLE:
            return NOT_APPLICABLE

        if self.right_type.match(right_value, left_value):
            return left_value

        raise IntersectionNotFound


class SetXValueType(ValueType):
    def __init__(self, left_type, right_type):
        self.left_type = left_type
        self.right_type = right_type

    def join_values(self, left_value, right_value):
        """Return intersection of two values."""
        try:
            return WILD_CARD.get_intercect(left_value, right_value)
        except IntersectionNotFound:
            pass

        if left_value is NOT_APPLICABLE and right_value is NOT_APPLICABLE:
            return NOT_APPLICABLE

        if self.left_type.match(left_value, right_value):
            return right_value

        raise IntersectionNotFound


class SetXSetType(ConditionType):
    def __init__(self, left_type, right_type):
        self.left_type = left_type
        self.right_type = right_type

    def join_values(self, left_value, right_value):
        """Return intersection of two values."""
        try:
            return WILD_CARD.get_intercect(left_value, right_value)
        except IntersectionNotFound:
            pass

        if left_value is NOT_APPLICABLE and right_value is NOT_APPLICABLE:
            return NOT_APPLICABLE

        return lambda x: (self.left_type.match(left_value, x) and
                          self.right_type.match(right_value, x))


class IntersectionNotFound(Exception):
    """Used for internal controls."""


class _WildCard:
    """An object that equals with any value.

    The wild card is represented with '*' in table texts.

    In the module this object is used from ``WILD_CARD`` variable,
    do not create a object directly.
    """

    directive = '*'

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
        return self.directive

    def __repr__(self):
        """Return 'WILD_CARD'."""
        return 'WILD_CARD'

    @staticmethod
    def get_intercect(a, b):
        if a is WILD_CARD and b is WILD_CARD:
            return WILD_CARD
        if a is WILD_CARD:
            return b
        if b is WILD_CARD:
            return a
        raise IntersectionNotFound


WILD_CARD = _WildCard()
"""The WILD_CARD object. This is unique in the module."""


class _NotApplicable:
    """The non-applicable value.

    The non-applicable value is represented with 'N/A' in table texts.

    The object does not equal with any value.

    In the module this object is used from ``NOT_APPLICABLE`` variable,
    do not create a object directly.
    """

    directive = 'N/A'

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
        return self.directive

    def __repr__(self):
        """Return 'NOT_APPLICABLE'."""
        return 'NOT_APPLICABLE'


NOT_APPLICABLE = _NotApplicable()
"""The NOT_APPLICABLE object. This is unique in the module."""


def estimate_format(lines):
    """Estimate the format of the table text.

    The lines should be removed leading/trailing white lines and indents.
    Use strip_lines function.

    :pram lines: lines of the table text
    :return: estimated table format
    """
    for fmt in (ReSTSimpleTable, ReSTGridTable, MarkdownTable):
        if fmt.can_accept(lines):
            return fmt

    raise TableMarkupError('The table format is unknown.')


class ReSTTable:
    """Sckeleton implementation of reStructuredText tables.

    In this class common logic between ReSTSimpleTable and ReSTGridTable
    is written. Both of them use the docutils package.
    """

    @staticmethod
    def can_accept(lines, line_pattern):
        """Check if the first/last line match the pattern."""
        if len(lines) < 3:
            return False

        first_line = lines[0]
        last_line = lines[-1]

        if (re.match(line_pattern, first_line) and
                re.match(line_pattern, last_line)):
            return True
        return False

    @staticmethod
    def parse(lines, parser):
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


class ReSTSimpleTable:
    """reStructuredText Simple Table."""

    @staticmethod
    def can_accept(lines):
        """Judge if the table is estimated to be this format."""
        return ReSTTable.can_accept(lines, r'^ *[= ]*= *$')

    @staticmethod
    def parse(lines):
        r"""Parse reStructuredText SimpleTable.

        :param lines: lines of a table text
        :type text: string
        :return: tuple of list of labels and list of row values

        :Example:

            >>> ReSTSimpleTable.parse('''\
            ... ==== ====
            ...  A    B
            ... ==== ====
            ...  a1   b1
            ...  a2   b2
            ... ==== ====
            ... '''.splitlines())
            (['A', 'B'], [['a1', 'b1'], ['a2', 'b2']])

            >>> ReSTSimpleTable.parse('''\
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
        return ReSTTable.parse(lines, DocutilsSimpleTableParser())


class ReSTGridTable:
    """reStructuredText Grid Table."""

    @staticmethod
    def can_accept(lines):
        """Judge if the table is estimated to be this format."""
        return ReSTTable.can_accept(lines, r'^ *\+[-\+]*-\+ *$')

    @staticmethod
    def parse(lines):
        r"""Parse reStructuredText Grid Table.

        :Example:

            >>> ReSTGridTable.parse('''\
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
        return ReSTTable.parse(lines, DocutilsGridTableParser())


class MarkdownTable:
    """Markdown Table."""

    @staticmethod
    def can_accept(lines):
        """Judge if the table is estimated to be this format."""
        if len(lines) < 3:
            return False
        if re.match(r' *\|? *[-:]+[-| :]*\|? *$', lines[1]):
            return True
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

    @classmethod
    def parse(cls, lines):
        r"""Parse a Markdown table.

        :Example:

            >>> MarkdownTable.parse('''\
            ... |  A  |  B  |  C  |
            ... |-----|:--- | ---:|
            ... |  a  |  b  |  c  |
            ... |  1  |  2  |  3  |
            ... '''.splitlines())
            (['A', 'B', 'C'], [['a', 'b', 'c'], ['1', '2', '3']])

        """
        split_cell = cls.__split_cell
        header = split_cell(lines[0])
        body = [split_cell(line) for line in lines[2:]]
        return header, body


class TableMarkupError(ValueError):
    """Exception about a table text format."""
