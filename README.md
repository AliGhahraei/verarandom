# verarandom

[![Build Status](https://travis-ci.org/AliGhahraei/verarandom.svg?branch=master)
](https://travis-ci.org/AliGhahraei/verarandom)
[![codecov](https://codecov.io/gh/AliGhahraei/verarandom/branch/master/graph/badge.svg)
](https://codecov.io/gh/AliGhahraei/verarandom)

True random numbers (provided by random.org) in Python

# Usage
This module provides a random.Random subclass, so it implements all [random functions](https://docs.python.org/3/library/random.html) (excluding [Bookkeeping functions](https://docs.python.org/3/library/random.html#bookkeeping-functions)) with true randomness. It requires an internet connection to work and will raise a ConnectionError if the server doesn't respond or a VeraRandomError if there is another problem with the request.

```python
>>> from verarandom import VeraRandom
>>> r = VeraRandom()

>>> r.randint(1, 10, n=5)  # You may specify the number of integers to request
[3, 4, 10, 3, 7]
>>> r.randint(-10, 3)
-2
>>> r.choice(['rock', 'paper', 'scissors'])
'scissors'
```
