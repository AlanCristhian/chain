"""Chain is a tiny tool for performing data transformation and data analysis
by successive function calls and successive generator consumption. For example:

>>> from chain import given, ANS
>>> given("abcd")(reversed)(c.upper() for c in ANS)(list).end
['D', 'C', 'B', 'A']

The 'reversed' function runs with "abcd" as argument. Then the generator
expression iterates over the 'ANS' constant. 'ANS' stores the result returned
for 'reversed'. At next, the generator turns each character in the string
to uppercase. Then calls the 'list' function whit the generator. Finally,
lookups the '.end' property that stores the result of the execution.
"""

import collections.abc
import dis
import functools
import types


__all__ = ["ANS", "Link", "given", "unpack", "Cascade"]


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


# This class will be used to store the output of the
# previous call if ANS is used in a generator expression.
#
# See the NOTE [1]
class _PreviousGenerator:
    def __init__(self):
        self.ANS = None

    def __next__(self):
        return next(self.ANS)


# Implements the minimun protocol to have an iterable.
class _LastAnswer:
    """This constant will be used to collect the output of the previous
    function or store the previous generator defined in the chain.
    """

    def __iter__(self):
        return _PreviousGenerator()

    def __repr__(self):
        return "ANS"


ANS = _LastAnswer()


class Link:
    """Implements the successive call pattern. Allways returns itself.

    >>> link = Link("abcd")
    >>> link(reversed)
    <Link object at 0x7fe2a91b6f28>
    >>> link(list) is link
    True
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

        # NOTE: In CPython, all generator expressions stores the iterable of
        # the first "for statement" in a local constant called ".0", the
        # "dot zero" constant.
        if isinstance(generator.gi_frame.f_locals[".0"], _PreviousGenerator):

            # NOTE [1]: Now the current generator can iterate
            # over the output of the previous call
            generator.gi_frame.f_locals[".0"].ANS = iter(self.end)

            # Now the result of this function is the
            # input of the next instruction in the chain.
            self.end = generator
        else:
            description = "Can not iterate over '%s', 'ANS' constant only."
            class_name = generator.gi_frame.f_locals[".0"].__class__.__name__
            raise ValueError(description % class_name)
        return self

    # lookup the property of the last answer
    def __getattr__(self, attribute):
        method = getattr(self.end, attribute)
        def wrapper(*args, **kwargs):

            # Now the result of this function is the
            # input of the next instruction in the chain.
            self.end = method(*args, **kwargs)
            return self
        functools.update_wrapper(wrapper, method)
        return wrapper


def given(obj):
    """Returns a object that implement the successive calls pattern.

    >>> given("abcd")(reversed)(list).end
    ['d', 'c', 'b', 'a']
    """

    return Link(obj)


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


def unpack(obj, function):
    """Call the function with the upacket
    object and return their result.

    >>> add = lambda a, b: a + b

    >>> args = (1, 2)
    >>> assert unpack(args, add) == add(*args)

    >>> kwargs = dict(a=1, b=2)
    >>> assert unpack(kwargs, add) == add(**kwargs)
    """

    if isinstance(obj, collections.abc.Mapping):
        return function(**obj)
    elif isinstance(obj, collections.abc.Sequence):
        return function(*obj)
    else:
        return function(obj)
