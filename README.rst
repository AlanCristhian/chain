=====
Chain
=====

**Chain** is a tiny tool for performing data transformation and data
analysis by *successive function calls* and *successive generator*
*consumption*. For example: ::

    >>> from chain import given, ANS
    >>> given("abcd")(reversed)(c.upper() for c in ANS)(list).end
    ['D', 'C', 'B', 'A']

The ``reversed`` function runs with ``"abcd"`` as argument. Then the generator
expression iterates over the ``ANS`` constant. ``ANS`` stores the result
returned for ``reversed``. At next, the generator turns each character in
the string to uppercase. Then call the ``list`` function whit the generator.
Finally, lookup the ``.end`` property that stores the result of the execution.

.. contents:: Table of Contents

------------
Installation
------------

 ::

    $ pip install git+https://github.com/AlanCristhian/chain.git

--------
Tutorial
--------

Successive Function Calls
=========================

Executes a function with the given object: ::

    >>> from chain import given
    >>> given(1)(lambda x: x + 2).end
    3

The ``given`` function call the *lambda function* with ``1`` as argument. The
``.end`` property returns the result of the execution.

You can compose multiple functions by successive calls: ::

    >>> (given([1.5, 2.5, 3.9])
    ...     (max)
    ...     (round)
    ...     (lambda x: x + 2)
    ... .end)
    6

Each function sourounded by parenthesis is called with the result of the
precedent function as argument. The below construction is equivalent to. ::

    >>> _ = [1.5, 2.5, 3.9]
    >>> _ = max(_)
    >>> _ = round(_)
    >>> (lambda x: x + 2)(_)
    6

Call Functions With Multiples Arguments
=======================================

You can pass multiples arguments to each function. The first argument of the
succesive call should be a *Callable*. The *Callable* passed as argument
is executed whit the output of the previous call as first argument, and the
passed argument as second. E.g.: ::

    >>> add = lambda x, y: x + y
    >>> given(10)(add, 20).end
    30

The *lambda function* assign ``10`` value to ``x`` and ``20`` to ``y``. You can
do the same with as many arguments as you want: ::

    >>> add_3_ints = lambda x, y, z: x + y + z
    >>> given(10)(add_3_ints, 20, 30).end
    60

The ``ANS`` Constant
====================

In all previous examples the *lambda function* is executed with the object
returned by the previous call as first argument. What if you want to pass the
returned object as second, third, or any order? You can use the ``ANS``
constant: ::

    >>> from chain import given, ANS
    >>> given('Three')(lambda x, y, z: x + y + z, 'One', 'Two', ANS).end
    'OneTwoThree'

The ``ANS`` constant is like the ``ans`` key in scientific calculators. They
stores the output of the previous operation.

You can use the ``ANS`` constant as multiple times as you want: ::

    >>> given('o')(lambda x, y, z: x + y + z, ANS, ANS, ANS).end
    'ooo'

*Keyword arguments* are allowed: ::

    >>> given("a")(lambda x, y, z: x + y + z, y="b", z="c").end
    'abc'
    >>> given("c")(lambda x, y, z: x + y + z, x="a", y="b", z=ANS).end
    'xyz'

Successive Generator Consumption
================================

If you pass a *generator expression* as unique argument, you can consume
those *generators* successively. ::

    >>> (given([1, 2, 3])
    ...     (i*2 for i in ANS)
    ...     (i*3 for i in ANS)
    ...     (list)
    ... .end)
    [6, 12, 18]

The ``given`` function can only consume those generators that iterates over the
``ANS`` constant: ::

    >>> given("abc")(i for i in (1, 2))(list).end
    ValueError: Can not iterate over 'tuple_iterator', 'ANS' constant only.

What if you want to do some like?: ::

    >>> (given("abc")
    ...     ((i, j) for i, j in enumerate(ANS))
    ...     (list)
    ... .end)
    ValueError: Can not iterate over 'enumerate', 'ANS' constant only.

To do that you must call the ``enumerate`` function first. ::

    >>> (given("abcd")
    ...     (enumerate)
    ...     ((i, j) for i, j in ANS)
    ...     (list)
    ... .end)
    [('a', 0), ('b', 1), ('c', 2), ('d', 3)]

Another limitation is that you can not iterate over "nested for statements": ::

    >>> (given("abc")
    ...     (i + j for i in ANS for j in "xyz")
    ...     (list)
    ... .end)
    SyntaxError: "Multiple for statements" are not allowed.

To do that you should use the ``product`` function of the ``itertools``
module. ::

    >>> from itertools import product
    >>> (given("abc")
    ...     (product, "xyz", ANS)
    ...     (i + j for i, j in ANS)
    ...     (list)
    ... .end)
    ['xa', 'xb', 'xc', 'ya', 'yb', 'yc', 'za', 'zb', 'zc']

Reuse The Methods Of The Returned Object
========================================

You can lookup and call the methods of the given and returned object: ::

    char = (given("abc")
            .upper()  # 1
            (list)    # 2
            .pop()    # 3
           ).end

    assert char == 'A'

1. Call the ``upper`` method of ``'abc'``. It give ``'ABC'``.
2. Executes the ``list`` built-in function with ``'ABC'``. It give
   ``['A', 'B', 'C']``.
3. Call the ``pop`` method of the list created in step 2. Returns ``'A'``.

Handle Multiples Returned Objects
=================================

Sometimes you want to pass more than one argument to the next function. In that
cases you can use a list and acces to each object by index: ::

    >>> from chain import given, ANS
    >>> (given([1, 2, 3])
    ...     (lambda x: x[0] + x[1] + x[2])
    ... .end)
    >>> 6

Or you can use a dict. ::

    >>> (given(dict(a=1, b=2, c=3))
    ...     (lambda x: x['a'] + x['b'] + x['c'])
    ... .end)
    >>> 6

The same problem can be solved with the ``unpack`` function: ::

    >>> from chain import given, unpack
    >>> sum_list = (given([1, 2, 3])
    ...     (unpack, lambda a, b, c: a + b + c)
    ... .end)
    >>> sum_list
    6

Method cascading
================

In november of 2013 Steven D'Aprano was
`created a recipe <http://code.activestate.com/recipes/578770-method-chaining/>`_
to allow method cascading. Method cascading is an apy which allows multiple
methods to be called on the same object.

For example, supose that you want to call multiple methods of the same object like: ::

    items = []

    items.append(2)
    items.append(1)
    items.reverse()
    items.append(3)

    assert items == [1, 2, 3]

The chain ``chain`` have the ``Cascade`` class that turns any object into
one with methods that can be chained. ::

    from chain import Cascade

    items = (
        Cascade([])
        .append(2)
        .append(1)
        .reverse()
        .append(3)
    ).end

    assert items == [1, 2, 3]

-----------------
API Documentation
-----------------

given(obj) -> Link
==================

Returns a ``Link`` instance that implement the successive calls pattern. ::

    >>> link = given("abcd")
    >>> link
    <Link object at 0x7fe2ab0b29d8>


function unpack(obj, function)
==============================

Call the function with the upacket object and returns their result.::

    >>> add = lambda a, b: a + b

    >>> args = (1, 2)
    >>> assert unpack(args, add) == add(*args)  # 3

    >>> kwargs = dict(a=1, b=2)
    >>> assert unpack(kwargs, add) == add(**kwargs)  # 3

class Link(instruction, \*args, \*\*kwargs)
===========================================

Implements the successive call pattern. Allways returns itself. ::

    >>> link = Link("abcd")
    >>> link(reversed)
    <Link object at 0x7fe2a91b6f28>
    >>> link(list) is link
    True

attribute Link.end
==================

Stores the result of the execution. ::

    >>> link = Link("abcd")(reversed)(list)
    >>> link
    <Link object at 0x7fe2a91b6f28>
    >>> link.end
    ['D', 'C', 'B', 'A']

constant ANS
============

This constant should be used to collect the output of the previous function or
store the previous generator defined in the chain. See the tutorial for more
info.

class Cascade(obj)
==================

An adapter class which turns any object into one with methods that can be
chained. ::

    >>> from chain import Cascade
    >>> result = Cascade([]).append(2).append(1).reverse().append(3).end
    >>> result
    [1, 2, 3]
