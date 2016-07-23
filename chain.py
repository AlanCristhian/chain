"""
Chain is a tiny tool for performing data transformation and data analysis
by successive function calls and successive generator consumption. For example:

>>> from chain import given, ANS
>>> given("abcd")(reversed)(c.upper() for c in ANS)(list).end
['D', 'C', 'B', 'A']

The 'reversed' function runs with '"abcd"' as argument. Then the generator
expression iterates over the 'ANS' constant. 'ANS' stores the result returned
for 'reversed'. At next, the generator converts each character in the string
to uppercase. Then calls the 'list' function whit the generator. Finally,
lookups the '.end' property that stores the result of the execution.
"""

import collections.abc
import dis
import functools
import inspect
import types


__all__ = ["LastAnswer", "ANS", "Link", "given", "Function", "WithGiven"]


# In CPython, all generator expressions stores the iterable of the first
# "for statement" in a local constant called ".0", the "dot zero" constant.
#
# This function returns a copy of the `generator` argument and
# replaces their "dot zero" constant with the `iterable` object.
def _replace_dot_zero(generator, iterable, old_locals):
    generator_function = types.FunctionType(
        generator.gi_code,
        generator.gi_frame.f_globals,
        generator.__name__
    )

    # Creates a new `dict` because `old_locals` is inmutable.
    new_locals = {**old_locals, ".0": iterable}

    # Creates and returns a new "generator object".
    generator_object = generator_function(**new_locals)
    return generator_object


# Check if the generator have more than one "for statement".
def _have_nested_for_statement(generator) -> bool:
    matched = [True for instruction in dis.get_instructions(generator)
               if instruction.opname == "FOR_ITER"]
    return True if len(matched) > 1 else False


# Replace each `ANS` item in the tuple with the given `obj`
def _replace_ans_in_args(obj, args: tuple) -> bool:
    return (obj if item is ANS else item for item in args)


# Replace each `ANS` value in the dict with the given `obj`
def _replace_ans_in_kwargs(obj, kwargs: dict) -> dict:
    return {key: obj if value is ANS else value
            for (key, value) in kwargs.items()}


# Transforms a method into a single-dispatch generic method.
def _single_dispatch_method(function):
    dispatcher = functools.singledispatch(function)
    def wrapper(*args, **kw):
        return dispatcher.dispatch(args[1].__class__)(*args, **kw)
    wrapper.register = dispatcher.register
    functools.update_wrapper(wrapper, function)
    return wrapper


# Yields all global variables in the higher (calling) frames
def _get_outer_globals(frame):
    while frame:
        yield frame.f_globals
        frame = frame.f_back


# Yields all locals variables in the higher (calling) frames
def _get_outer_locals(frame):
    while frame:
        yield frame.f_locals
        frame = frame.f_back


# Implements the minimun protocol to have an iterable.
class LastAnswer:
    """
    This constant will be used to collect the output of the previous
    function or store the previous generator defined in the chain.
    """
    def __iter__(self):
        # Returns itself because I want to check identity later.
        return self

    def __next__(self):
        pass


ANS = LastAnswer()


class Link:
    """
    If `instruction` is a Callable, call them with `args` and
    `kwargs`. Store `instruction` in `ANS` if it is a Generator.
    """
    def __init__(self, obj):
        self.end = obj

    # Raises an error if the instruction is not a callable or generator.
    @_single_dispatch_method
    def __call__(self, instruction, *args, **kwargs):
        description = "Expected 'callable' or 'generator'. Got '%s'"
        raise TypeError(description % instruction.__class__.__name__)

    # Evaluates the function instruction.
    @__call__.register(collections.abc.Callable)
    def _(self, function, *args, **kwargs):
        has_ans_constant = False
        if ANS in args:
            has_ans_constant = True
            args = _replace_ans_in_args(self.end, args)
        if ANS in kwargs.values():
            has_ans_constant = True
            kwargs = _replace_ans_in_kwargs(self.end, kwargs)

        # Now the result of this function is the
        # input of the next instruction in the chain.
        if has_ans_constant:
            self.end = function(*args, **kwargs)
        else:
            self.end = function(self.end, *args, **kwargs)
        return self

    # Consumes the generator instruction.
    @__call__.register(collections.abc.Generator)
    def _(self, generator, *args, **kwargs):
        if args or kwargs:
            description = "Can not accept arguments if you pass "\
                          "a generator at first (%d given)."
            count = len(args) + len(kwargs)
            raise TypeError(description % count)
        if _have_nested_for_statement(generator):
            raise SyntaxError("Multiple for statement are not allowed.")
        old_locals = generator.gi_frame.f_locals
        if isinstance(old_locals[".0"], LastAnswer):

            # Now the result generator is the input
            # of the next instruction in the chain.
            self.end = _replace_dot_zero(generator, iter(self.end), old_locals)
        else:
            description = "Can not iterate over '%s', 'ANS' constant only."
            class_name = old_locals[".0"].__class__.__name__
            raise ValueError(description % class_name)
        return self


def given(obj) -> Link:
    """
    Return a class that implement the successive calls pattern.
    """
    return Link(obj)


class Function:
    """
    A class that behaves like a function. and stores
    the name and quality name of the instance.
    """
    def __init__(self, stack):
        self.stack = stack
        self._name = None
        self.__qualname__ = "chain.Function"

    def __call__(self, obj):
        operation = Link(obj)
        for instruction, args, kwargs in self.stack:
            operation(instruction, *args, **kwargs)
        return operation.end

    # Find the name of the current object in the given scope
    def _find_name_in_scope(self, scope):
        for variables in scope:
            for name, value in variables.items():
                if value is self:
                    return name

    # find the name of the current object
    def _find_name(self, current_frame):
        outer_locals = _get_outer_locals(current_frame)
        name = self._find_name_in_scope(outer_locals)
        if name is None:
            outer_globals = _get_outer_globals(current_frame)
            name = self._find_name_in_scope(outer_globals)
        if name is None:
            return self.__qualname__
        else:
            return name

    @property
    def __name__(self):
        if self._name is None:
            upper_frame = inspect.currentframe().f_back
            self._name = self._find_name(upper_frame)
        return self._name

    def __repr__(self):
        if self._name is None:
            upper_frame = inspect.currentframe().f_back
            self._name = self._find_name(upper_frame)
        if self._name == self.__qualname__:
            return "<%s object at 0x%02x>" % (self._name, hash(self))
        else:
            return "<function %s at 0x%02x>" % (self._name, hash(self))


class WithGiven:
    """
    Creates function using the successive function call pattern.

    >>> from operator import add, mul
    >>> operation = WithGiven(add, 2)(mul, 3).end
    >>> operation
    <function operation at 0x7f83828a508>
    >>> operation(1)
    9
    """
    def __init__(self, instruction, *args, **kwargs):
        self.stack = []
        self.stack.append((instruction, args, kwargs))

    def __call__(self, instruction, *args, **kwargs):
        """
        Adds operations to the stack of instructions.
        """
        self.stack.append((instruction, args, kwargs))
        return self

    @property
    def end(self):
        """
        Creates and returns the function.
        """
        return Function(self.stack)
