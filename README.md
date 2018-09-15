# verarandom

[![PyPI version](https://badge.fury.io/py/verarandom.svg)](https://badge.fury.io/py/verarandom)
[![Build Status](https://travis-ci.org/AliGhahraei/verarandom.svg?branch=master)
](https://travis-ci.org/AliGhahraei/verarandom)
[![codecov](https://codecov.io/gh/AliGhahraei/verarandom/branch/master/graph/badge.svg)
](https://codecov.io/gh/AliGhahraei/verarandom)

True random numbers in Python.

Full documentation: https://alighahraei.github.io/verarandom/

# Usage
This module provides random.Random subclasses, so they implement all [random functions](
https://docs.python.org/3/library/random.html) (except [Bookkeeping functions](
https://docs.python.org/3/library/random.html#bookkeeping-functions)) with true randomness. They
require an internet connection to work and will either raise a ConnectionError or a subclass of
verarandom.errors.VeraRandomError for validation failures and other related error conditions.

```python
>>> from verarandom import RandomOrg
>>> r = RandomOrg()

>>> r.quota_estimate
1000000
>>> r.randint(1, 10, n=5)
[3, 4, 10, 3, 7]
>>> r.quota_estimate  # bits were deducted from quota
999986

>>> r.randint(3, 5, n=1)
[5]
>>> r.randint(-10, 3)  # a single number (like random.randint)
-2

>>> r.random()
0.040120765652295
>>> r.choice(['rock', 'paper', 'scissors'])
'scissors'
```
