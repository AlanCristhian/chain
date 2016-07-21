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
>>> last = [1.5, 2.5, 3.9]
>>> last = max(last)
>>> last = round(last)
>>> (lambda x: x + 2)(last)
6
```

### Use functions with more than one argument

You can pass arguments to each function. The first argument of the succesive
call should be a *Callable* or *Generator*. The *Callable* passed as argument
is executed whit the output of the previous call as first argument and the
passed argument as second. E.g

```python
>>> add = lambda x, y: x + y
>>> given(10)(add, 20).end
30
```

The *lambda function* assign the `10` value to the `x` and `20` to `y`. You can
do the same with as many arguments as you want:

```python
>>> given(10)(lambda x, y, z: x + y + z, 20, 30).end
60
```

### The `ANS` constant

In all previous examples the *lambda function* is executed with object returned
by the previous call as firs argument. What if you want to pass the returned
object as second, third or any order? You can use the `ANS` constant:

```python
>>> from chain import given, ANS
>>> given('Three')(lambda a, b, c: a + b + c, 'One', 'Two', ANS).end
'OneTwoThree'
```

The `ANS` constant is like the ```ans``` key in scientific calculators. `ANS`
is by "last **ans**wer". They stores the output of the previous operation.

You can use the `ANS` constant as many times as you want:

```python
>>> given('o')(lambda x, y, z: x + y + z, ANS, ANS, ANS).end
'ooo'
```

*Keyword arguments* are great because you do not need to remember the argument
order. So, *keyword arguments* are allowed:

```python
>>> given("a")(lambda x, y, z: x + y + z, y="b", z="c").end
'abc'
>>> given("z")(lambda x, y, z: x + y + z, x="x", y="y", z=ANS).end
'xyz'
```

You can use `ANS` if you want to be more explicit

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

The `given` object can only consume those generators that iterate over the
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
ValueError: Can not iterate over 'range', 'ANS' constant only.
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


### Reuse successive calls object

In case that you want to reutilize a set of operations over an generic object,
chain provide the `with_given_obj` function:

```python
>>> from chain import with_given_obj, ANS
>>> add_3_to_even = (with_given_obj
...                     (n for n in ANS if n%2 == 0)
...                     (n + 3 for n in ANS)
...                     (list)
...                 .end)
>>> add_3_to_even([1, 2, 3, 4, 5, 6])
[5, 7, 9]
```

All functions created with the `with_given_obj` function can only accept one
postional argument.

-------------------------------------------------------------------------------

## API Documentation

### function `given(obj: Any) -> given.<locals>.link`
### function `given(obj):`

Return a function that implement the successive calls pattern.

```python
>>> operation = given("abcd")    # <-- here
>>> operation
<function given.<locals>.link at 0x7fe2ab0b29d8>
```

### funcion `given.<locals>.link(instruction: Callable[...], *args: Tuple[Any], **kwargs: Dict[str, Any]) -> given.<locals>.link`
### funcion `given.<locals>.link(instruction: Generator, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> given.<locals>.link`
### funcion `given.<locals>.link(instruction, *args, **kwargs)`

Implement the successive call patern.

```python
>>> operation = given("abcd")
>>> operation
<function given.<locals>.link at 0x7fe2ab0b29d8>
>>> operation(reversed)(list)    # <-- here
<function given.<locals>.link at 0x7fe2a91b6f28>
```

### property `given.<locals>.link.end  #Type: Any`
### property `given.<locals>.link.end`

Store the result of the execution.

```python
>>> operation = given("abcd")
>>> operation
<function given.<locals>.link at 0x7fe2ab0b29d8>
>>> operation(reversed)(list).end    # <-- here
['D', 'C', 'B', 'A']
```

### function `with_given_obj(instruction: Callable[...]) -> with_given_obj.<locals>.link`
### function `with_given_obj(instruction: Generator) -> with_given_obj.<locals>.link`
### function `with_given_obj(instruction)`

Define a function by successive calls pattern.

```python
>>> from operator import add, mul
>>> operation = with_given_obj(add, 2)(mul, 3)    # <-- here
<function with_given_obj.<locals>.link at 0x7fe2a919c048>
```

### property `with_given_obj.<locals>.link.end  #Type: Callable[[Any], Any]`
### property `with_given_obj.<locals>.link.end`

Store the function created with `with_given_obj`.

### constant `ANS  #Type: Iterable[Any]`
### constant `ANS`

This constant will be used to collect the output of the previous
function or store the previous generator defined in the chain.

-------------------------------------------------------------------------------

## API Documentation

### class `Given(obj: Any) -> Link`
### class `Given(obj)`

Return a class that implement the successive calls pattern.

```python
>>> link = Given("abcd")    # <-- here
>>> link
<Link object at 0x7fe2ab0b29d8>
```

### class `Link(instruction: Callable[...], *args: Tuple[Any], **kwargs: Dict[str, Any]) -> Link`
### class `Link(instruction: Generator, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> Link`
### class `Link(instruction, *args, **kwargs)`

Implement the successive call pattern. Allways retunrn a `Link` object.

```python
>>> link = given("abcd")(reversed)(list)
<Link object at 0x7fe2a91b6f28>
```

### property `Link.end  #Type: Any`
### property `Link.end`

Store the result of the execution.

```python
>>> link = given("abcd")(reversed)(list)
>>> link.end    # <-- here
['D', 'C', 'B', 'A']
```

### function `WithGivenObject(instruction: Callable[...]) -> WithGivenObject`
### function `WithGivenObject(instruction: Generator) -> WithGivenObject`
### function `WithGivenObject(instruction)`

Define a function by successive calls pattern.

```python
>>> from operator import add, mul
>>> operation = WithGivenObject(add, 2)(mul, 3)    # <-- here
<WithGivenObject object at 0x7fe2a919c048>
```

### property `WithGivenObject.end  #Type: Callable[[Any], Any]`
### property `WithGivenObject.end`

Store the function created with `WithGivenObject`.

### constant `ANS  #Type: Iterable[Any]`
### constant `ANS`

This constant will be used to collect the output of the previous
function or store the previous generator defined in the chain.
