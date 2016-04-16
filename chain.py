"""
Implement a data transformer by chain calls like pipes. E.g:

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


__all__ = ["given", "LAST", "with_given_obj"]


def _copy_and_replace_dot_zero(generator, iterable):
    # Return a copy of the `generator` argument and replace
    # their "dot zero" constant with the `iterable` object.
    return FunctionType(
        generator.gi_code,
        generator.gi_frame.f_globals,
        generator.__name__
    )(**{**generator.gi_frame.f_locals, ".0": iterable})


class _Last:
    # Implement the minimun protocol to have an iterable object.
    def __iter__(self):
        return self

    def __next__(self):
        pass


LAST = _Last()


def _check_for_iter_count(generator):
    # Raise SyntaxError if the generator have more than
    # one "for statement". Do noting if have only one.
    code = generator.gi_code.co_code
    i = 9
    n = len(code) - 7
    while i < n:
        op = code[i]
        if op >= 90:
            if op == 93:  # FOR_ITER
                raise SyntaxError("Multiple for statement are not supported.")
            i += 3
        else:
            i += 1


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
        nonlocal obj
        if callable(instruction):
            have_previous = False
            if LAST in args:
                have_previous = True
                args = (obj if a == LAST else a for a in args)
            if LAST in kwargs.values():
                have_previous = True
                for key, value in kwargs.items():
                    if value == LAST:
                        kwargs[key] = obj
            if have_previous:
                obj = instruction(*args, **kwargs)
            else:
                obj = instruction(obj, *args, **kwargs)
        elif isinstance(instruction, GeneratorType):
            if args or kwargs:
                message = "Can not get arguments if you pass a generator "\
                          "at first (%d given)."
                count = len(args) + len(kwargs)
                raise TypeError(message % count)
            _check_for_iter_count(instruction)
            dot_zero = instruction.gi_frame.f_locals[".0"]
            if isinstance(dot_zero, _Last):
                obj = _copy_and_replace_dot_zero(instruction, iter(obj))
            else:
                message = "Can not iterate over '%s', 'LAST' constant only."
                raise ValueError(message % dot_zero.__class__.__name__)
        else:
            message = "Expected 'callable' or 'generator'. Got '%s'"
            raise TypeError(message % instruction.__class__.__name__)
        # Store accumaled operations result in .end property
        link.end = obj
        return link
    return link


def _function(stack):
    # Create a function that execute each instruction
    # in the `stack` with the given argument `obj`.
    def function(obj):
        """
        Execute each instruction in the chain.
        """
        operation = given(obj)
        for instruction, args, kwargs in stack:
            operation(instruction, *args, **kwargs)
        return operation.end
    return function


def with_given_obj(instruction, *args, **kwargs):
    """
    Define a function by successive calls pattern.
    """
    stack = []
    append = stack.append
    append((instruction, args, kwargs))
    def link(instruction, *args, **kwargs):
        """
        Add operations to the stack of instructions.
        """
        append((instruction, args, kwargs))
        return link
    link.end = _function(stack)
    return link
