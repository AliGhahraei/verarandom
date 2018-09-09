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

>>> r.remaining_quota
1000000
>>> r.randint(1, 10, n=5)
[3, 4, 10, 3, 7]
>>> r.remaining_quota  # bits are deducted from quota
999986

>>> r.randint(-10, 3)  # A call without the number of integers returns 1, not a list
-2

>>> r.choice(['rock', 'paper', 'scissors'])
'scissors'
```
