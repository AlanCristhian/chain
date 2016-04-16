# chain

*Chain* is a framework for performing data transformation and
data analysis pipelines by *successive function calls* and
*successive generator consumption*.

## Installation

```shell
$ pip install git+https://github.com/AlanCristhian/chain.git
```

## Tutorial

### Successive call with functions

Execute a function with the given object:

```python
>>> from chain import given
>>> given(15)(lambda x: x + 15).end
30
```

The `given` function execute the *lambda function* with `15` as argument. The
`.end` property return the result of the execution.

You can chain function execution by successive calls:

```python
>>> from chain import given
>>> given([1.5, 2.5, 3.9])(max)(round)(lamba x: x**10).end
1048576
```

Each function sourounded by parenthesis is called with the result of the
precedent function as argument. The below construction is equivalent to.

```python
>>> last = [1.5, 2.5, 3.9]
>>> last = max(last)
>>> last = round(last)
>>> (lambda x: x**10)(last)
1048576
```

Also is the same that:

```python
>>> (lambda x: x**10)(round(max([1.5, 2.5, 3.9])))
1048576
```

If you compare the two next lines of code, you can see that the first
sentence is nested, and the second is flat.

```python
(lambda x: x**10)(round(max([1.5, 2.5, 3.9])))
given([1.5, 2.5, 3.9])(max)(round)(lamba x: x**10).end
```

Also, the execution order of the first line is from right to left. In the
second line, the order of execution is from left to right, like the english
language lecture order.

`given` try to solve the same problems that those libraries that implement the
*method chaining pattern*. The issue with *method chaining* is that you can
chain only methos defined in the class that use such pattern.

The *successive calls pattern* let you chain any function or any method of any
object. In the example bellow, I use the `upper` method of the `str` class.

```python
>>> given('abc')(str.upper).end
'ABC'
```

Here an example with the `operator` module:

```python
>>> import operator
>>> given(10)(operator.pow, 3)(operator.truediv, 2)(operator.sub, 200).end
300
```

As you can see in the previous example, you can pass arguments to each
function. The first argument of the succesive call should be a *Callable* or
*Generator*. The *Callable* passed as argument is executed whit the output of
the previous call as first argument and the passed argument as second. E.g

```python
>>> given(10)(lambda x, y: x + y, 20).end
30
```

The *lambda function* assign the `10` value to the `x` and `20` to `y`. You can
do the same with as many arguments as you want:

```python
>>> given(10)(lambda x, y, z: x + y + z, 20, 30).end
60
```

Maybe you observe that the *lambda function* is executed with object returned
by the previous call as firs argument. What if you want to pass the returned
object as second, third or any order? You can use the `LAST` constant:

```python
>>> from chain import given, LAST
>>> given('Three')(lambda a, b, c: a + b + c, 'One', 'Two', LAST).end
'OneTwoThree'
```

The `LAST` constant is like the `ans` key in scientific calculators.

You can use the `LAST` constant as many times as you want:

```python
>>> given('o')(lambda x, y, z: x + y + z, LAST, LAST, LAST).end
'ooo'
```

*Keyword arguments* are great because you do not need to remember the argument
order. So, *keyword arguments* are allowed:

```python
>>> given("a")(lambda x, y, z: x + y + z, y="b", z="c").end
'abc'
>>> given("z")(lambda x, y, z: x + y + z, x="x", y="y", z=LAST).end
'xyz'
```

Another common pattern is pyping via the Unix `|` symbol. At next I show you
a [recipe published by Steven D'Aprano.](http://code.activestate.com/recipes/580625-collection-pipeline-in-python/)

```python
class Apply:
    def __init__(self, func):
        self.func = func
    def __ror__(self, iterable):
        return self.func(iterable)

Reverse = Apply(reversed)
List = Apply(list)
```

```python
>>> "abcd" | Reverse | List
['d', 'c', 'b', 'a']
```

But, what if you want to use a function that take more than one argument like
zip function? You can't do this with function composition or piping.

Succesive function call sovles such problem:

```python
>>> given("abcd")(zip, LAST, range(4))(list).end
[('a', 0), ('b', 1), ('c', 2), ('d', 3)]
```

### Successive generator consumption

If you pass a *generator expression* as first argument, you can consume
those *generators* successively.

```python
>>> given([1, 2, 3])(i*2 for i in LAST)(i*3 for i in LAST)(list).end
[6, 12, 18]
```

The `given` object can only consume those generators that iterate over the
`LAST` constant:

```python
>>> given("abc")(i for i in [1, 2])(list).end
...
ValueError: Can not iterate over 'list_iterator', 'LAST' constant only.
```

What if you want to do some like:

```python
>>> given(10)(i for i in range(LAST))(list).end
...
ValueError: Can not iterate over 'range', 'LAST' constant only.
>>> given("abc")(i for i in enumerate(LAST))(list).end
...
ValueError: Can not iterate over 'enumerate', 'LAST' constant only.
```

To do that you must call the `range` or `enumerate` function first.

```python
>>> given(10)(range)(i for i in LAST)(list).end
[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
>>> given("abc")(enumerate)(i for i in LAST)(list).end
[(0, "a"), (1, "b"), (2, "c")]
```

Another limitation is that you can not iterate over "nested for statements":

```python
>>> given("abc")(i + j for i in LAST for j in "xyz")(list).end
SyntaxError: "Multiple for statement are not supported."
```

**But**, you can use the `product` function of the `itertools` module.

```python
>>> from itertools import product
>>> from chain import given, LAST
>>> given("abc")(product, "xyz", LAST)(i + j for i, j in LAST)(list).end
['xa', 'xb', 'xc', 'ya', 'yb', 'yc', 'za', 'zb', 'zc']
```

### Reuse successive calls object

In case that you want to reutilize a set of operations over an generic object,
chain provide the `with_given_obj` function:

```python
>>> from chain import with_given_obj, LAST
>>> add_2_to_even = (with_given_obj
...     (n for n in LAST if n%2 == 0)
...     (n + 2 for n in LAST)
...     (list)
... .end)
>>> add_2_to_even([1, 2, 3, 4, 5, 6])
[4, 6, 8]
```
