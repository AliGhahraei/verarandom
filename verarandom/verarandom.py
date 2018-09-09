from enum import Enum, IntEnum
from random import Random
from typing import List, Dict, Union, Optional

from requests import get


RANDOM_ORG_URL = 'https://www.random.org'
QUOTA_URL = f'{RANDOM_ORG_URL}/quota'
INTEGER_URL = f'{RANDOM_ORG_URL}/integers'

QUOTA_LIMIT = 0
MAX_QUOTA = 1_000_000

MAX_INTEGER_LIMIT = int(1e9)
MIN_INTEGER_LIMIT = int(-1e9)
MAX_NUMBER_OF_INTEGERS = int(1e4)

FORMAT = 'format'
PLAIN_FORMAT = 'plain'


class RandintsToFloatOptions(IntEnum):
    """ random.org's API doesn't offer floats, but a sequence of integers can emulate this. """
    RANDINTS_QUANTITY = 3
    RANDINTS_NUMBER_OF_DIGITS = 5


class RandintRequestFields(Enum):
    RANDOMIZATION = 'rnd'
    TRULY_RANDOM = 'new'
    BASE = 'base'
    BASE_10 = '10'
    NUM = 'num'
    MIN = 'min'
    MAX = 'max'
    COL = 'col'


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


class VeraRandom(Random):
    """ True random (random.org) number generator implementing the random.Random interface. """
    def __init__(self):
        self._remaining_quota = None
        super().__init__()

    @property
    def remaining_quota(self):
        self._request_quota_if_unset()
        return self._remaining_quota

    def _request_quota_if_unset(self):
        if self._remaining_quota is None:
            self.request_quota()

    def request_quota(self) -> int:
        """ Request bit quota from random.org """
        self._remaining_quota = int(self._make_plain_text_request(QUOTA_URL))
        return self._remaining_quota

    def seed(self, *args, **kwargs):
        """ Empty definition. """

    def getstate(self):
        """ Not implemented. """
        raise NotImplementedError

    def setstate(self, state):
        """ Not implemented. """
        raise NotImplementedError

    def check_quota(self):
        """ If IP can't make requests, raise BitQuotaExceeded. Called before generating numbers. """
        self._request_quota_if_unset()

        if self.remaining_quota < QUOTA_LIMIT:
            raise BitQuotaExceeded(self.remaining_quota)

    def check_randint_request_parameters(self, a: int, b: int, n: int):
        """ Check parameters for a random request and potentially raise RandomRequestFieldError. """
        self._check_number_of_randints(n)
        self._check_randint_range(a, b)

    @staticmethod
    def _check_randint_range(a: int, b: int):
        if a > MAX_INTEGER_LIMIT or b > MAX_INTEGER_LIMIT:
            raise RandomNumberLimitTooLarge(b)
        if a < MIN_INTEGER_LIMIT or b < MIN_INTEGER_LIMIT:
            raise RandomNumberLimitTooSmall(a)

    @staticmethod
    def _check_number_of_randints(n: int):
        if n < 1:
            raise NoRandomNumbersRequested
        if n > MAX_NUMBER_OF_INTEGERS:
            raise TooManyRandomNumbersRequested(n)

    def random(self) -> float:
        """ Generate a random float by using integers as its fractional part.

        [06, 11, 21] => 0.061121
        """
        number_of_digits = RandintsToFloatOptions.RANDINTS_NUMBER_OF_DIGITS.value
        max_int = int('9' * number_of_digits)

        randints = self.randint(0, max_int, RandintsToFloatOptions.RANDINTS_QUANTITY.value)
        zero_padded_ints = (str(randint).zfill(number_of_digits) for randint in randints)
        return float(f"0.{''.join(zero_padded_ints)}")

    def randint(self, a: int, b: int, n: Optional[int] = None) -> Union[List[int], int]:
        """ Generates n integers as a list or as a single integer if no n is given. """
        n_or_default = 1 if n is None else n
        numbers_as_string = self._make_randint_request(a, b, n_or_default)
        integers = [int(random) for random in numbers_as_string.splitlines()]
        self._remaining_quota -= sum(integer.bit_length() for integer in integers)

        return integers if n else integers[0]

    def _make_randint_request(self, a: int, b: int, n: int) -> str:
        self.check_randint_request_parameters(a, b, n)
        params = self._create_randint_request_params(a, b, n)
        numbers_as_string = self._make_random_request(INTEGER_URL, params=params)
        return numbers_as_string

    @staticmethod
    def _create_randint_request_params(a: int, b: int, n: int) -> Dict:
        return {RandintRequestFields.RANDOMIZATION.value: RandintRequestFields.TRULY_RANDOM.value,
                RandintRequestFields.BASE.value: RandintRequestFields.BASE_10.value,
                RandintRequestFields.MIN.value: a, RandintRequestFields.MAX.value: b,
                RandintRequestFields.NUM.value: n, RandintRequestFields.COL.value: 1}

    @staticmethod
    def _make_plain_text_request(url: str, params: Optional[Dict] = None) -> str:
        params = params or {}
        response = get(url, params={FORMAT: PLAIN_FORMAT, **params})
        response.raise_for_status()

        return response.text

    def _make_random_request(self, *args, **kwargs) -> str:
        self.check_quota()
        return self._make_plain_text_request(*args, **kwargs)
