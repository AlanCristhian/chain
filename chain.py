"""Chain is a tiny tool for performing data transformation and data analysis
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
import collections
import dis
import functools
import types

import name


__all__ = ["ANS", "Link", "given", "Function", "Instruction", "nmspc",
           "UNPACK", "Cascade", "Map"]


# In CPython, all generator expressions stores the iterable of the first
# "for statement" in a local constant called ".0", the "dot zero" constant.
#
# This function returns a copy of the `generator` argument and
# replaces their "dot zero" constant with the `iterable` object.
def _fix_dot_zero(generator, iterable, old_locals):
    generator_function = types.FunctionType(
        generator.gi_code,
        generator.gi_frame.f_globals,
        generator.__name__)

    # Creates a new `dict` because `old_locals` is inmutable.
    new_locals = {**old_locals, ".0": iterable}

    # Creates and returns a new "generator object".
    return generator_function(**new_locals)


# Check if the generator have more than one "for statement".
def _have_nested_for_statement(generator):
    matched = [True for instruction in dis.get_instructions(generator)
               if instruction.opname == "FOR_ITER"]
    return True if len(matched) > 1 else False


# Replace each `ANS` item in the tuple with the given `obj`
def _replace_ans_in_args(obj, args):
    return (obj if item is ANS else item for item in args)


# Replace each `ANS` value in the dict with the given `obj`
def _replace_ans_in_kwargs(obj, kwargs):
    return {key: obj if value is ANS else value
            for (key, value) in kwargs.items()}


# Transforms a method into a single-dispatch generic method.
def _single_dispatch_method(method):
    dispatcher = functools.singledispatch(method)

    def wrapper(*args, **kwargs):
        if len(args) > 1:
            return dispatcher.dispatch(args[1].__class__)(*args, **kwargs)
        else:
            # An args tuple with only one element means that the user
            # is trying to lookup a property of the last answer.
            return args[0]

    wrapper.register = dispatcher.register
    functools.update_wrapper(wrapper, method)
    return wrapper


# A base class for all constants of this module
class _Protocol(name.AutoName):
    def __repr__(self):
        return "<protocol %s at %#02x>" % (self.__assigned_name__, hash(self))


# Implements the minimun protocol to have an iterable.
class _LastAnswer(_Protocol):
    """This constant will be used to collect the output of the previous
    function or store the previous generator defined in the chain.
    """
    def __iter__(self):

        # Returns itself because I want to check identity later.
        return self

    def __next__(self):
        pass


ANS = _LastAnswer()


class _Unpack(_Protocol):
    """ Indicates that the next funciton in the chain should
    unpack the result of the previous function in the chain.
    """


UNPACK = _Unpack()


class Link:
    """If `instruction` is a Callable, call them with `args` and
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

    # Creates a Generator with the last answer as iterable.
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
        if old_locals[".0"] is ANS:

            # Now the fixed generator is the input
            # of the next instruction in the chain.
            self.end = _fix_dot_zero(generator, iter(self.end), old_locals)
        else:
            description = "Can not iterate over '%s', 'ANS' constant only."
            class_name = old_locals[".0"].__class__.__name__
            raise ValueError(description % class_name)
        return self

    # The next call of function will unpack the last answer
    @__call__.register(_Unpack)
    def _(self, obj):
        def unpacker(function, *args, **kwargs):
            """Unpack the last answer."""
            if isinstance(self.end, collections.abc.Mapping):
                self.end = function(**self.end)
            elif isinstance(self.end, collections.abc.Sequence):
                self.end = function(*self.end)
            else:
                self.end = function(self.end)
            return self
        return unpacker

    # lookup the property of the last answer
    def __getattr__(self, attribute):
        method = getattr(self.end, attribute)
        def wrapper(*args, **kwargs):
            self.end = method(*args, **kwargs)
            return self
        functools.update_wrapper(wrapper, method)
        return wrapper


@functools.singledispatch
def given(obj):
    """Return a object that implement the successive calls pattern."""
    return Link(obj)


@given.register(type(Ellipsis))
def _(obj):
    """Return a class that creates function using
    the successive function call pattern.
    """
    return Instruction


class Function(name.AutoName):
    """A class that behaves like a function."""
    def __init__(self, stack):
        super().__init__()
        self._stack = stack
        self.__qualname__ = "chain.Function"

    def __call__(self, obj):
        operation = Link(obj)
        for instruction, args, kwargs in self._stack:
            operation(instruction, *args, **kwargs)
        return operation.end

    @property
    def __name__(self):
        return self.__assigned_name__

    def __repr__(self):
        return "<function %s at %#02x>" % (self.__assigned_name__, hash(self))


class Instruction:
    """Creates a function using the successive function call pattern.

    >>> from operator import add, mul
    >>> operation = Instruction(add, 2)(mul, 3).end
    >>> operation
    <function operation at 0x7f83828a508>
    >>> operation(1)
    9
    """
    def __init__(self, instruction, *args, **kwargs):
        self._stack = [(instruction, args, kwargs)]

    def __call__(self, instruction, *args, **kwargs):
        """Adds operations to the stack of instructions."""
        self._stack.append((instruction, args, kwargs))
        return self

    @property
    def end(self):
        """Creates and returns the function."""
        return Function(self._stack)


class nmspc(collections.UserDict):
    """A simple attribute-based namespace.
    >>> from chain import nmspc
    >>> n = nmspc(a=1, b=22, c=333)
    >>> n
    nmspc(a=111, b=222, c=333)
    >>> n.a
    111
    >>> n.b
    222
    >>> n.c
    333

    This object is a subclass of the dict type.

    >>> isinstance(nmspc, dict)
    True
    """
    def __getattr__(self, attribute):
        return self[attribute]

    def __dir__(self):
        return list(self.keys())

    def __repr__(self):
        elements = ", ".join("%s=%r" % (key, value)
                             for key, value in self.items())
        return "nmspc(%s)" % elements


class Cascade:
    """ An adapter class which turns any object
    into one with methods that can be chained.

    >>> from chain import Cascade
    >>> result = Cascade([]).append(2).append(1).reverse().append(3).end
    >>> result
    [1, 2, 3]
    """
    def __init__(self, obj):
        self.end = obj

    def __getattr__(self, name):
        attr = getattr(self.end, name)
        if callable(attr):
            def selfie(*args, **kwargs):
                # Call the method just for side-effects, return self.
                attr(*args, **kwargs)
                return self
            return selfie
        else:
            return attr


class Map:
    def __init__(self, function):
        self._function = function
        self._arguments = []

    def __call__(self, *args, **kwargs):
        self._arguments.append([args, kwargs])
        return self

    @property
    def end(self):
        for args, kwargs in self._arguments:
            self._function(*args, **kwargs)
