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

import dis
import types


__all__ = ["given", "ANS", "with_given_obj", "Given", "WithGivenObject"]


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
    return generator_function(**new_locals)


# Implements the minimun protocol to have an iterable.
class _LastAnswer:
    def __iter__(self):
        return self  # Returns itself because I want to check identity later.

    def __next__(self):
        pass


# This constant will be used to collect the output of the previous
# function or store the previous generator defined in the chain.
ANS = _LastAnswer()


# Return True if the generator have more than one "for statement".
def _have_nested_for_statement(generator):
    matched = [True for instruction in dis.get_instructions(generator)
               if instruction.opname == "FOR_ITER"]
    return True if len(matched) > 1 else False


# Replace each `ANS` item with the given `obj`
def _replace_ans_in_args(obj, args):
    return (obj if item is ANS else item for item in args)


# Replace each `ANS` value with the given `obj`
def _replace_ans_in_kwargs(obj, kwargs):
    return {key: obj if value is ANS else value
            for (key, value) in kwargs.items()}


class Link:
    """
    If `instruction` is a Callable, call them with `args` and
    `kwargs`. Store `instruction` in `ANS` if it is a Generator.
    """
    def __init__(self, obj):
        self.end = obj

    def __call__(self, instruction, *args, **kwargs):
        if callable(instruction):
            has_ans_constant = False
            if ANS in args:
                has_ans_constant = True
                args = _replace_ans_in_args(self.end, args)
            if ANS in kwargs.values():
                has_ans_constant = True
                kwargs = _replace_ans_in_kwargs(self.end, kwargs)
            if has_ans_constant:
                result = instruction(*args, **kwargs)
            else:
                result = instruction(self.end, *args, **kwargs)

        elif isinstance(instruction, types.GeneratorType):
            if args or kwargs:
                description = "Can not accept arguments if you pass "\
                              "a generator at first (%d given)."
                count = len(args) + len(kwargs)
                raise TypeError(description % count)
            if _have_nested_for_statement(instruction):
                raise SyntaxError("Multiple for statement are not allowed.")
            old_locals = instruction.gi_frame.f_locals
            if isinstance(old_locals[".0"], _LastAnswer):
                result = _replace_dot_zero(instruction, iter(self.end), old_locals)
            else:
                description = "Can not iterate over '%s', 'ANS' constant only."
                class_name = old_locals[".0"].__class__.__name__
                raise ValueError(description % class_name)

        else:
            description = "Expected 'callable' or 'generator'. Got '%s'"
            raise TypeError(description % instruction.__class__.__name__)

        # Now the result of this function is the
        # input of the next function in the chain.
        self.end = result

        return self


# class Given:
#     def __init__(self, obj):
#         self.link = Link(obj)

#     def __call__(self, instruction, *args, **kwargs):
#         return self.link(instruction, *args, **kwargs)

def Given(obj: Any) -> Link:
    return Link(obj)


def given(obj):
    """
    Implement successive calls pattern. E.g.

    >>> given("abcd")(reversed)(list).end
    ['d', 'c', 'b', 'a']
    """
    def link(instruction, *args, **kwargs):
        """
        If `instruction` is a Callable, call them with `args` and
        `kwargs`. Store `instruction` in `ANS` if it is a Generator.
        """

        # I use the `obj` closure to pass the output of the current
        # function as input of the next function in the chain.
        #
        # The `nonlocal` statement allow me change the content of `obj`.
        nonlocal obj

        if callable(instruction):
            has_ans_constant = False
            if ANS in args:
                has_ans_constant = True
                args = _replace_ans_in_args(obj, args)
            if ANS in kwargs.values():
                has_ans_constant = True
                kwargs = _replace_ans_in_kwargs(obj, kwargs)
            if has_ans_constant:
                result = instruction(*args, **kwargs)
            else:
                result = instruction(obj, *args, **kwargs)

        elif isinstance(instruction, types.GeneratorType):
            if args or kwargs:
                description = "Can not accept arguments if you pass "\
                              "a generator at first (%d given)."
                count = len(args) + len(kwargs)
                raise TypeError(description % count)
            if _have_nested_for_statement(instruction):
                raise SyntaxError("Multiple for statement are not allowed.")
            old_locals = instruction.gi_frame.f_locals
            if isinstance(old_locals[".0"], _LastAnswer):
                result = _replace_dot_zero(instruction, iter(obj), old_locals)
            else:
                description = "Can not iterate over '%s', 'ANS' constant only."
                class_name = old_locals[".0"].__class__.__name__
                raise ValueError(description % class_name)

        else:
            description = "Expected 'callable' or 'generator'. Got '%s'"
            raise TypeError(description % instruction.__class__.__name__)

        # Store accumated operations result in the `.end` property.
        link.end = result

        # Now the result of this function is the
        # input of the next function in the chain.
        obj = result

        return link
    return link


# Create a function that execute each instruction
# in the `stack` with the given argument `obj`.
def _function(stack):
    def function(obj):
        """
        Execute each instruction in the chain with the given object.
        """
        operation = given(obj)
        for instruction, args, kwargs in stack:
            operation(instruction, *args, **kwargs)
        return operation.end
    return function


class WithGivenObject:
    def __init__(self, instruction, *args, **kwargs):
        self.stack = []
        self.append = self.stack.append
        self.append((instruction, args, kwargs))

    def __call__(self, instruction, *args, **kwargs):
        """
        Add operations to the stack of instructions.
        """
        self.append((instruction, args, kwargs))
        return self

    def __getattr__(self, attribute):
        if attribute in self.__dict__.keys():
            return self.__dict__[attribute]
        else:
            def function(obj):
                """
                Execute each instruction in the chain with the given object.
                """
                operation = Link(obj)
                for instruction, args, kwargs in self.stack:
                    operation(instruction, *args, **kwargs)
                return operation.end
            function.__qualname__ = attribute
            function.__name__ = attribute
            return function

    @property
    def end(self):
        def function(obj):
            """
            Execute each instruction in the chain with the given object.
            """
            operation = Link(obj)
            for instruction, args, kwargs in self.stack:
                operation(instruction, *args, **kwargs)
            return operation.end
        return function


def with_given_obj(instruction, *args, **kwargs):
    """
    Define a function by successive calls pattern.

    >>> from operator import add, mul
    >>> operation = with_given_obj(add, 2)(mul, 3).end
    >>> operation(1)
    9
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
