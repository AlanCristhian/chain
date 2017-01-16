# Chain

**Chain** is a tiny tool for performing data transformation and data
analysis by *successive function calls* and *successive generator*
*consumption*. For example:

```python
>>> from chain import given, ANS
>>> given("abcd")(reversed)(c.upper() for c in ANS)(list).end
['D', 'C', 'B', 'A']
```

The `reversed` function runs with `"abcd"` as argument. Then the generator
expression iterates over the `ANS` constant. `ANS` stores the result returned
for `reversed`. At next, the generator turns each character in the string
to uppercase. Then call the `list` function whit the generator. Finally,
lookup the `.end` property that stores the result of the execution.

## Table Of Contents

- [Installation](#installation)
- [Tutorial](#tutorial)
    - [Successive Function Calls](#successive-calls)
    - [Call Functions With Multiples Arguments](#many-arguments)
    - [The ANS Constant](#ans-constant)
    - [Successive Generator Consumption](#generator-consumption)
    - [Reuse The Methods Of The Returned Object](#reuse-methods)
    - [Handle Multiples Returned Objects](#return-multiple)
    - [Method cascading](#method-cascading)
- [API Documentation](#api)
    - [function given(obj) -> Link](#given-obj)
    - [function unpack(obj, function)](#unpack)
    - [class Link(instruction, \*args, \*\*kwargs)](#link)
    - [property Link.end](#link-end)
    - [constant ANS](#ans)
    - [class Cascade(obj)](#cascade)

## Installation <a name="installation"></a>

```shell
$ pip install git+https://github.com/AlanCristhian/chain.git
```

## Tutorial <a name="tutorial"></a>

### Successive Function Calls <a name="successive-calls"></a>

Executes a function with the given object:

```python
>>> from chain import given
>>> given(1)(lambda x: x + 2).end
3
```

The `given` function call the *lambda function* with `1` as argument. The
`.end` property returns the result of the execution.

You can compose multiple functions by successive calls:

```python
>>> (given([1.5, 2.5, 3.9])
...     (max)
...     (round)
...     (lambda x: x + 2)
... .end)
6
```

Each function sourounded by parenthesis is called with the result of the
precedent function as argument. The below construction is equivalent to.

```python
>>> _ = [1.5, 2.5, 3.9]
>>> _ = max(_)
>>> _ = round(_)
>>> (lambda x: x + 2)(_)
6
```

### Call Functions With Multiples Arguments <a name="many-arguments"></a>

You can pass multiples arguments to each function. The first argument of the
succesive call should be a *Callable*. The *Callable* passed as argument
is executed whit the output of the previous call as first argument, and the
passed argument as second. E.g.:

```python
>>> add = lambda x, y: x + y
>>> given(10)(add, 20).end
30
```

The *lambda function* assign `10` value to `x` and `20` to `y`. You can
do the same with as many arguments as you want:

```python
>>> add_3_ints = lambda x, y, z: x + y + z
>>> given(10)(add_3_ints, 20, 30).end
60
```

### The `ANS` Constant <a name="ans-constant"></a>

In all previous examples the *lambda function* is executed with the object
returned by the previous call as first argument. What if you want to pass the
returned object as second, third, or any order? You can use the `ANS` constant:

```python
>>> from chain import given, ANS
>>> given('Three')(lambda x, y, z: x + y + z, 'One', 'Two', ANS).end
'OneTwoThree'
```

The `ANS` constant is like the ```ans``` key in scientific calculators. They
stores the output of the previous operation.

You can use the `ANS` constant as multiple times as you want:

```python
>>> given('o')(lambda x, y, z: x + y + z, ANS, ANS, ANS).end
'ooo'
```

*Keyword arguments* are allowed:

```python
>>> given("a")(lambda x, y, z: x + y + z, y="b", z="c").end
'abc'
>>> given("c")(lambda x, y, z: x + y + z, x="a", y="b", z=ANS).end
'xyz'
```

### Successive Generator Consumption <a name="generator-consumption"></a>

If you pass a *generator expression* as unique argument, you can consume
those *generators* successively.

```python
>>> (given([1, 2, 3])
...     (i*2 for i in ANS)
...     (i*3 for i in ANS)
...     (list)
... .end)
[6, 12, 18]
```

The `given` function can only consume those generators that iterates over the
`ANS` constant:

```python
>>> given("abc")(i for i in (1, 2))(list).end
ValueError: Can not iterate over 'tuple_iterator', 'ANS' constant only.
```

What if you want to do some like?:

```python
>>> (given("abc")
...     ((i, j) for i, j in enumerate(ANS))
...     (list)
... .end)
ValueError: Can not iterate over 'enumerate', 'ANS' constant only.
```

To do that you must call the `enumerate` function first.

```python
>>> (given("abcd")
...     (enumerate)
...     ((i, j) for i, j in ANS)
...     (list)
... .end)
[('a', 0), ('b', 1), ('c', 2), ('d', 3)]
```

Another limitation is that you can not iterate over "nested for statements":

```python
>>> (given("abc")
...     (i + j for i in ANS for j in "xyz")
...     (list)
... .end)
SyntaxError: "Multiple for statements" are not allowed.
```

To do that you should use the `product` function of the `itertools` module.

```python
>>> from itertools import product
>>> (given("abc")
...     (product, "xyz", ANS)
...     (i + j for i, j in ANS)
...     (list)
... .end)
['xa', 'xb', 'xc', 'ya', 'yb', 'yc', 'za', 'zb', 'zc']
```

### Reuse The Methods Of The Returned Object <a name="reuse-methods"></a>

You can lookup and call the methods of the given and returned object:

```python
char = (given("abc")
        .upper()  # 1
        (list)    # 2
        .pop()    # 3
       ).end

assert char == 'A'
```

1. Call the `upper` method of `'abc'`. It give `'ABC'`.
2. Executes the `list` built-in function with `'ABC'`. It give
   `['A', 'B', 'C']`.
3. Call the `pop` method of the list. Returns `'A'`.

### Handle Multiples Returned Objects <a name="return-multiple"></a>

Sometimes you want to pass more than one argument to the next function. In that
cases you can use a list and acces to each object by index:

```python
>>> from chain import given, ANS
>>> (given([1, 2, 3])
...     (lambda x: x[0] + x[1] + x[2])
... .end)
>>> 6
```

Or you can use a dict.

```python
>>> (given(dict(a=1, b=2, c=3))
...     (lambda x: x['a'] + x['b'] + x['c'])
... .end)
>>> 6
```

The same problem can be solved with the `unpack` function:

```python
>>> from chain import given, unpack
>>> sum_list = (given([1, 2, 3])
...     (unpack, lambda a, b, c: a + b + c)
... .end)
>>> sum_list
6
```

### Method cascading <a name="method-cascading"></a>

In november of 2013 Steven D'Aprano was
[created a recipe](http://code.activestate.com/recipes/578770-method-chaining/)
to allow method cascading. Method cascading is an apy which allows multiple
methods to be called on the same object.

For example, supose that you want to call multiple methods of the same object like:

```python
items = []

items.append(2)
items.append(1)
items.reverse()
items.append(3)

assert items == [1, 2, 3]
```

The chain ``chain`` have the ``Cascade`` class that turns any object into
one with methods that can be chained.

```python
from chain import Cascade

items = (
    Cascade([])
    .append(2)
    .append(1)
    .reverse()
    .append(3)
).end

assert items == [1, 2, 3]
```

## API Documentation <a name="api"></a>

### function given(obj) -> Link <a name="given-obj"></a>

Returns a `Link` instance that implement the successive calls pattern.

```python
>>> link = given("abcd")
>>> link
<Link object at 0x7fe2ab0b29d8>
```

### function unpack(obj, function) <a name="unpack"></a>

Call the function with the upacket object and returns their result.

```python
>>> add = lambda a, b: a + b

>>> args = (1, 2)
>>> assert unpack(args, add) == add(*args)  # 3

>>> kwargs = dict(a=1, b=2)
>>> assert unpack(kwargs, add) == add(**kwargs)  # 3
```

### class Link(instruction, \*args, \*\*kwargs) <a name="link"></a>

Implements the successive call pattern. Allways returns itself.

```python
>>> link = Link("abcd")
>>> link(reversed)
<Link object at 0x7fe2a91b6f28>
>>> link(list) is link
True
```

### attribute Link.end <a name="link-end"></a>

Stores the result of the execution.

```python
>>> link = Link("abcd")(reversed)(list)
>>> link
<Link object at 0x7fe2a91b6f28>
>>> link.end
['D', 'C', 'B', 'A']
```

### constant ANS <a name="ans"></a>

This constant should be used to collect the output of the previous function or
store the previous generator defined in the chain. See the tutorial for more
info.

### class Cascade(obj) <a name="cascade"></a>

An adapter class which turns any object into one with methods that can be
chained.

```python
>>> from chain import Cascade
>>> result = Cascade([]).append(2).append(1).reverse().append(3).end
>>> result
[1, 2, 3]
```
