from django.db.models import Aggregate, CharField, Value


class ArrayToString(Aggregate):
    function = "ARRAY_TO_STRING"
    template = "%(function)s(%(expressions)s)"
    output_field = CharField()

    def __init__(self, expression, delimiter, null_string, **extra):
        delimiter_expr = Value(str(delimiter))
        null_string_expr = Value(str(null_string))
        super().__init__(expression, delimiter_expr, null_string_expr, **extra)
