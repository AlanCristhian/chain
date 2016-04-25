"""
Implement a data transformation by successive calls like pipes. E.g:

>>> from operator import add, mul
>>> # python style
... print(mul(add(add(1, 2), 3), 4)
24
>>> # chained calls style
... from chain import given
>>> given(1)(add, 2)(add, 3)(mul, 4)(print)
24
"""


from types import GeneratorType, FunctionType


__all__ = ["given", "ANS"]


def _replace_dot_zero(generator, iterable):
    # Return a copy of the `generator` argument and replace
    # their "dot zero" local constant with the `iterable` object.
    return FunctionType(
        generator.gi_code,
        generator.gi_frame.f_globals,
        generator.__name__
    )(**{**generator.gi_frame.f_locals, ".0": iterable})


class _LastAnswer:
    # Implement the minimun protocol to have an iterable object.
    def __iter__(self):
        return self  # Return itself because I want to check identity later

    def __next__(self):
        pass


ANS = _LastAnswer()


def _have_nested_for_statement(generator):
    # This function return true if the generator have more
    # than one "for statement". Return false if have only one.
    code = generator.gi_code.co_code
    # The first nine bytes are equal in the code of all
    # generator expressions. Also, the fourth byte is
    # the op code of the first FOR_ITER. So, I start
    # the count of all FOR_ITER int the nineth byte.
    i = 9
    # Like after, the last seven bytes in the code of all generator
    # expressions are the same and are different than FOR_ITER op
    # code .So, I end the count seven position less than code length.
    n = len(code) - 7
    while i < n:
        op = code[i]
        if op >= 90:
            if op == 93:  # FOR_ITER
                return True
            i += 3
        else:
            i += 1
    return False


def _replace_ans_in_args(obj, args):
    # replace each `ANS` item with the given `obj`
    return (obj if item is ANS else item for item in args)


def _replace_ans_in_kwargs(obj, kwargs):
    # if a key have the `ANS` constant as value, replace it value with `obj`
    right_values = {key: obj for key, value in kwargs.items() if value is ANS}
    return {**kwargs, **right_values}


def given(obj):
    """
    Implement successive calls pattern. E.g.
    >>> given([1.5, 2.5, 3.9])(max)(round)(lamba x: x**10).end
    1048576
    """
    def link(instruction, *args, **kwargs):
        """
        If `instruction` is a Callable, call them with `args`
        and `kwargs`. Consume `instruction` if it is a Generator.
        """
        nonlocal obj  # this statement let me modify the content of `obj`
        if callable(instruction):
            have_ans = False
            if ANS in args:
                have_ans = True
                args = _replace_ans_in_args(obj, args)
            if ANS in kwargs.values():
                have_ans = True
                kwargs = _replace_ans_in_kwargs(obj, kwargs)
            if have_ans:
                result = instruction(*args, **kwargs)
            else:
                result = instruction(obj, *args, **kwargs)
        elif isinstance(instruction, GeneratorType):
            if args or kwargs:
                message = "Can not get arguments if you pass a generator "\
                          "at first (%d given)."
                count = len(args) + len(kwargs)
                raise TypeError(message % count)
            if _have_nested_for_statement(instruction):
                raise SyntaxError("Multiple for statement are not supported.")
            dot_zero = instruction.gi_frame.f_locals[".0"]
            if isinstance(dot_zero, _LastAnswer):
                result = _replace_dot_zero(instruction, iter(obj))
            else:
                message = "Can not iterate over '%s', 'ANS' constant only."
                raise ValueError(message % dot_zero.__class__.__name__)
        else:
            message = "Expected 'callable' or 'generator'. Got '%s'"
            raise TypeError(message % instruction.__class__.__name__)
        # Store accumated operations result in the `.end` property. Also, the
        # `obj` closure of the next call is now the `result` of this call.
        link.end = obj = result
        return link
    return link
