from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from functools import wraps
from random import Random
from typing import Optional, Union, List, Any, Callable

import requests

from verarandom.errors import (
    BitQuotaExceeded, NoRandomNumbersRequested, TooManyRandomNumbersRequested,
    RandomNumberLimitTooLarge, RandomNumberLimitTooSmall, HTTPError,
)


@dataclass(frozen=True)
class RandomConfig:
    # noinspection PyUnresolvedReferences
    """ Configuration used by :py:class:`verarandom.Verarandom`

    :param MAX_INTEGER: maximum integer that may be requested
    :param MIN_INTEGER: minimum integer that may be requested
    :param MAX_NUMBER_OF_INTEGERS: integers limit for a single request
    :param MAX_NUMBER_OF_FLOATS: floats limit for a single request
    """
    MAX_INTEGER: int
    MIN_INTEGER: int
    MAX_NUMBER_OF_INTEGERS: int
    MAX_NUMBER_OF_FLOATS: int


def reraise_request_errors(f: Callable):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except requests.HTTPError as e:
            raise HTTPError(str(e)) from e

    return wrapper


class VeraRandom(Random, metaclass=ABCMeta):
    """ :py:class:`abc.ABC` for random number services.

    Subclasses calculate true random numbers using a suitable online service. This class provides
    parameter validation using a configuration with minimum and maximum allowed values.
    """
    def __init__(self, config: RandomConfig):
        """
        :param config: values to use in parameter validation
        """
        self.config = config
        super().__init__()

    def seed(self, *args, **kwargs):
        """ Empty definition. """

    def getstate(self) -> None:
        """ Empty definition. """

    def setstate(self, _):
        """ Empty definition. """

    def random(self, n: Optional[int] = None) -> Union[List[float], float]:
        """ Similar to :py:func:`randint` """
        return self._generate_randoms(self._request_randoms, max_n=self.config.MAX_NUMBER_OF_FLOATS,
                                      n=n)

    def randint(self, a: int, b: int, n: Optional[int] = None) -> Union[List[int], int]:
        """ Generate n numbers as a list or a single one if no n is given.

        n is used to minimize the number of requests made and return type changes to be compatible
        with :py:mod:`random`'s interface
        """
        max_n = self.config.MAX_NUMBER_OF_INTEGERS
        return self._generate_randoms(self._request_randints, max_n=max_n, a=a, b=b, n=n)

    @abstractmethod
    def _request_randoms(self, n: int) -> List[float]:
        """ (Abstract) request numbers using already validated parameters.

        Not meant to be used directly by subclasses.
        """

    @abstractmethod
    def _request_randints(self, a: int, b: int, n: int) -> List[int]:
        """ Similar to :py:func:`_request_randoms` """

    def _generate_randoms(self, requester: Callable, *, max_n: int, n: int, **req_kwargs):
        n_or_default = 1 if n is None else n
        self._check_random_parameters(max_n, n_or_default, **req_kwargs)
        randoms = self._make_random_request(requester, **req_kwargs, n=n_or_default)
        return randoms if n else randoms[0]

    def _check_random_parameters(self, max_n: int, n: int, a: Optional[int] = None,
                                 b: Optional[int] = None):
        if a and b:
            self._check_random_range(a, b)
        self._check_number_of_randoms(n, max_n)

    def _check_random_range(self, a: int, b: int):
        if a > self.config.MAX_INTEGER or b > self.config.MAX_INTEGER:
            raise RandomNumberLimitTooLarge(b)
        if a < self.config.MIN_INTEGER or b < self.config.MIN_INTEGER:
            raise RandomNumberLimitTooSmall(a)

    @staticmethod
    def _check_number_of_randoms(n: int, max_: int):
        if n < 1:
            raise NoRandomNumbersRequested
        if n > max_:
            raise TooManyRandomNumbersRequested(n)

    @reraise_request_errors
    def _make_random_request(self, requester: Callable[..., List], **kwargs) -> List:
        return requester(**kwargs)


class VeraRandomQuota(VeraRandom, metaclass=ABCMeta):
    """ :py:class:`abc.ABC` for services with a limited number of bits per user like random.org

    Internally tracks a quota estimate by substracting each request's number of bits from the
    initial quota and verifies there are bits left before each request.

    NOTE: this class assumes it's the only one talking to the server when calculating its quota.
    """
    def __init__(self, config: RandomConfig, initial_quota: Optional[int] = None,
                 quota_limit: int = 0):
        """
        :param config: values to use in parameter validation
        :param initial_quota: last known quota
        :param quota_limit: minimum numbers of bits in quota to allow a request
        """
        self._remaining_quota = initial_quota
        self.quota_limit = quota_limit
        super().__init__(config)

    @property
    def quota_estimate(self) -> int:
        """ Approximately how many bits are left for the current user  """
        self._request_remaining_quota_if_unset()
        return self._remaining_quota

    @reraise_request_errors
    def request_quota(self) -> int:
        """ Request bit quota and store it """
        self._remaining_quota = self._request_quota()
        return self._remaining_quota

    @abstractmethod
    def _request_quota(self) -> int:
        """ (Abstract) Request quota to service. """

    @abstractmethod
    def _get_bits_spent(self, random_objects: List[Any]) -> int:
        """ (Abstract) calculate number of bits used for generating random objects.

        Function is used to subtract bits from the quota estimate.
        """

    def _make_random_request(self, requester: Callable[..., List], **kwargs) -> List:
        self._check_quota()
        randoms = super()._make_random_request(requester, **kwargs)
        self._remaining_quota -= self._get_bits_spent(randoms)
        return randoms

    def _request_remaining_quota_if_unset(self):
        if self._remaining_quota is None:
            self.request_quota()

    def _check_quota(self):
        """ If IP can't make requests, raise BitQuotaExceeded. Called before generating numbers. """
        self._request_remaining_quota_if_unset()
        if self.quota_estimate < self.quota_limit:
            raise BitQuotaExceeded(self.quota_estimate)
