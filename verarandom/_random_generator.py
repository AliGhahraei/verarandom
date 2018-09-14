from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from random import Random
from typing import Optional, Union, List, Any, Callable


class VeraRandomError(Exception):
    pass


class BitQuotaExceeded(VeraRandomError):
    """ IP has exceeded bit quota and should not be allowed to make further requests. """


class RandomRequestFieldError(VeraRandomError, ValueError):
    pass


class NoRandomNumbersRequested(RandomRequestFieldError):
    pass


class TooManyRandomNumbersRequested(RandomRequestFieldError):
    """ Attempted to request too many numbers to the generator's API """


class RandomNumberLimitTooLarge(RandomRequestFieldError):
    """ Max random number requested is too large for the generator's API """


class RandomNumberLimitTooSmall(RandomRequestFieldError):
    """ Min random number requested is too small for the generator's API """


@dataclass
class RandomConfig:
    QUOTA_LOWER_LIMIT: int
    MAX_INTEGER: int
    MIN_INTEGER: int
    MAX_NUMBER_OF_INTEGERS: int
    MAX_NUMBER_OF_FLOATS: int


class VeraRandom(Random, metaclass=ABCMeta):
    """ ABC for random number services. """
    def __init__(self, config: RandomConfig, initial_quota: Optional[int] = None):
        self.config = config
        self._remaining_quota = initial_quota
        super().__init__()

    @property
    def quota_estimate(self) -> int:
        self._request_remaining_quota_if_unset()
        return self._remaining_quota

    def seed(self, *args, **kwargs):
        """ Empty definition. """

    def getstate(self) -> None:
        """ Empty definition. """

    def setstate(self, _):
        """ Empty definition. """

    def random(self, n: Optional[int] = None) -> Union[List[float], float]:
        """ Generate n floats as a list or a single one if no n is given. """
        return self._generate_randoms(self._request_randoms, max_n=self.config.MAX_NUMBER_OF_FLOATS,
                                      n=n)

    def randint(self, a: int, b: int, n: Optional[int] = None) -> Union[List[int], int]:
        """ Generates n integers as a list or a single one if no n is given. """
        max_n = self.config.MAX_NUMBER_OF_INTEGERS
        return self._generate_randoms(self._request_randints, max_n=max_n, a=a, b=b, n=n)

    def request_quota(self) -> int:
        """ Request bit quota and store it. """
        self._remaining_quota = self._request_quota()
        return self._remaining_quota

    def _request_remaining_quota_if_unset(self):
        if self._remaining_quota is None:
            self.request_quota()

    def _generate_randoms(self, requester: Callable, *, max_n: int, n: int, **req_kwargs):
        n_or_default = 1 if n is None else n
        self._check_random_parameters(max_n, n_or_default, **req_kwargs)
        randoms = self._request_randoms_updating_quota(requester, **req_kwargs, n=n_or_default)
        return randoms if n else randoms[0]

    @abstractmethod
    def _request_quota(self) -> int:
        pass

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

    def _request_randoms_updating_quota(self, requester: Callable[..., List], **kwargs) -> List:
        self._check_quota()
        randoms = requester(**kwargs)
        self._remaining_quota -= self._get_bits_spent(randoms)
        return randoms

    def _check_quota(self):
        """ If IP can't make requests, raise BitQuotaExceeded. Called before generating numbers. """
        self._request_remaining_quota_if_unset()

        if self.quota_estimate < self.config.QUOTA_LOWER_LIMIT:
            raise BitQuotaExceeded(self.quota_estimate)

    @abstractmethod
    def _request_randoms(self, n: int) -> List[float]:
        pass

    @abstractmethod
    def _request_randints(self, a: int, b: int, n: int) -> List[int]:
        pass

    @abstractmethod
    def _get_bits_spent(self, randomly_generated_object: Any):
        pass
