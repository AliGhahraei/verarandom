# verarandom

[![Build Status](https://travis-ci.org/AliGhahraei/verarandom.svg?branch=master)
](https://travis-ci.org/AliGhahraei/verarandom)
[![codecov](https://codecov.io/gh/AliGhahraei/verarandom/branch/master/graph/badge.svg)
](https://codecov.io/gh/AliGhahraei/verarandom)

True random numbers (provided by random.org) in Python

# Usage
This module provides a random.Random subclass, so it implements all [random functions](
https://docs.python.org/3/library/random.html) (excluding [Bookkeeping functions](
https://docs.python.org/3/library/random.html#bookkeeping-functions)) with true randomness. It
requires an internet connection to work and will raise a ConnectionError if the server doesn't
respond, a requests.HTTPError or a subclass of verarandom.VeraRandomError if there is a problem 
with the request's parameters.

NOTE: this class assumes it's the only one talking to random.org when calculating its quota.

```python
>>> from verarandom import VeraRandom
>>> r = VeraRandom()

>>> r.remaining_quota
1000000
>>> r.randint(1, 10, n=5)
[3, 4, 10, 3, 7]
>>> r.remaining_quota  # bits were deducted from quota
999986

>>> r.randint(3, 5, n=1)
[5]
>>> r.randint(-10, 3)  # If no n is passed it returns a number, not a list (like the parent method)
-2

>>> r.random()
0.040120765652295
>>> r.choice(['rock', 'paper', 'scissors'])
'scissors'
```
