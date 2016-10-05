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
for `reversed`. At next, the generator converts each character in the string
to uppercase. Then calls the `list` function whit the generator. Finally,
lookups the `.end` property that stores the result of the execution.

## Installation

```shell
$ pip install git+https://github.com/AlanCristhian/name.git
$ pip install git+https://github.com/AlanCristhian/chain.git
```

## Tutorial

### Successive Function Calls

Executes a function with the given object:

```python
>>> from chain import given
>>> given(1)(lambda x: x + 2).end
3
```

The `given` function calls the *lambda function* with `1` as argument. The
`.end` property returns the result of the execution.

You can compose many functions by successive calls:

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

### Use functions with more than one argument

You can pass arguments to each function. The first argument of the succesive
call should be a *Callable*. The *Callable* passed as argument
is executed whit the output of the previous call as first argument and the
passed argument as second. E.g

```python
>>> add = lambda x, y: x + y
>>> given(10)(add, 20).end
30
```

The *lambda function* assign `10` value to `x` and `20` to `y`. You can
do the same with as many arguments as you want:

```python
>>> add_3 = lambda x, y, z: x + y + z
>>> given(10)(add_3, 20, 30).end
60
```

### The `ANS` constant

In all previous examples the *lambda function* is executed with the object
returned by the previous call as firs argument. What if you want to pass the
returned object as second, third or any order? You can use the `ANS` constant:

```python
>>> from chain import given, ANS
>>> given('Three')(lambda x, y, z: x + y + z, 'One', 'Two', ANS).end
'OneTwoThree'
```

The `ANS` constant is like the ```ans``` key in scientific calculators. They
stores the output of the previous operation.

You can use the `ANS` constant as many times as you want:

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

### Successive generator consumption

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

The `given` function can only consume those generators that iterate over the
`ANS` constant:

```python
>>> given("abc")(i for i in (1, 2))(list).end
ValueError: Can not iterate over 'tuple_iterator', 'ANS' constant only.
```

What if you want to do some like:

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

### Reuse the methods of the given object

You can use the methods in the given object:

```python
>>> given("abc").upper().end
'ABC'
```

### Reuse successive calls object

In case that you want to reutilize a set of operations over an generic object,
just pass the `...` constant as argument of the `given` function:

```python
>>> from chain import given, ANS
>>> add_3_to_even = (given(...)
...     (n for n in ANS if n%2 == 0)
...     (n + 3 for n in ANS)
...     (list)
... .end)
>>> add_3_to_even([1, 2, 3, 4, 5, 6])
[5, 7, 9]
```

### Handle many objects with the nmspc class

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
>>> from chain import given, ANS
>>> (given({'a': 1, 'b': 2, 'c': 3})
...     (lambda x: x['a'] + x['b'] + x['c'])
... .end)
>>> 6
```

Bot ways looks unintelligible. For this situation you can use the `nmspc` class
that is a tiny wrapper of the `types.SimpleNamespace` class of the standar
library.

```python
>>> from chain import given, ANS, nmspc
>>> (given(nmspc(a=1, b=2, c=3))
...     (lambda x: x.a + x.b + x.c)
... .end)
>>> 6
```

### Unpack the last answer

The same problem can be solved with the `UNPACK` constant:

```python
>>> from chain import given, UNPACK
>>> sum_list = (given([1, 2, 3])
...     (UNPACK)
...     (lambda x, y, z: x + y + z)
... .end)
>>> sum_list
6
```

## API Documentation

### function given(obj=...) -> Instruction

Returns the `Instruction` *class* if the `obj` argument is the `...` constant.

```python
>>> from operator import add, mul
>>> given(...)
<class 'chain.Instruction' at 0x11672c8>
```

### function given(obj) -> Link

Returns a `Link` instance that implement the successive calls pattern.

```python
>>> link = given("abcd")
>>> link
<Link object at 0x7fe2ab0b29d8>
```

### class Link(instruction, \*args, \*\*kwargs)

Implements the successive call pattern. Allways returns itself.

```python
>>> link = given("abcd")
>>> link(reversed)
<Link object at 0x7fe2a91b6f28>
>>> link(list) is link
True
```

### property Link.end

Stores the result of the execution.

```python
>>> link = given("abcd")(reversed)(list)
>>> link
<Link object at 0x7fe2a91b6f28>
>>> link.end
['D', 'C', 'B', 'A']
```

### class Instruction(instruction)

Stores a list of operations that will be performed with an object.

```python
>>> from operator import add, mul
>>> Instruction(add, 2)(mul, 3)
<Instruction object at 0x7fe2a919c048>
```

The `Instruction` callable allways returns itself.

```python
>>> from operator import add, mul
>>> instr = Instruction(add, 2)
>>> instr(mul, 3) is instr
True
```

### property Instruction.end

Store the function created with `Instruction`.

```python
>>> from operator import add, mul
>>> operation = Instruction(add, 2)(mul, 3).end
>>> operation
<function operation at 0x7f83828a508>
>>> operation(1)
9
```

### constant ANS

This constant should be used to collect the output of the previous function or
store the previous generator defined in the chain. See the tutorial for more
info.

### constant UNPACK

Indicates that the next funciton in the chain should unpack the result of the
previous function in the chain.

### class nmspc(\*\*kwargs)

A simple attribute-based namespace.

```python
>>> from chain import nmspc
>>> x = nmspc(a=1, b=22, c=333)
>>> x
nmspc(a=1, b=22, c=333)
>>> x.a
1
>>> x.b
22
>>> x.c
333
```
