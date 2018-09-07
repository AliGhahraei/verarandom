from enum import Enum, IntEnum
from random import Random
from typing import List, Dict, Optional, Union

from requests import get


RANDOM_ORG_URL = 'https://www.random.org'
QUOTA_URL = f'{RANDOM_ORG_URL}/quota'
INTEGER_URL = f'{RANDOM_ORG_URL}/integers'

QUOTA_LIMIT = 0
MAX_QUOTA = 1_000_000

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


class RandomOrgQuotaExceeded(Exception):
    """ IP has exceeded bit quota and should not be allowed to make further requests. """


class VeraRandom(Random):
    """ True random (random.org) number generator implementing the random.Random interface.
    """
    def __init__(self):
        quota = self._get_text_response(QUOTA_URL)

        self.remaining_quota = int(quota)
        super().__init__()

    def seed(self, _=None, **kwargs):
        pass

    def getstate(self):
        raise NotImplementedError

    def setstate(self, state):
        raise NotImplementedError

    def check_quota(self):
        """ Verify the user's IP can make requests. Should be called before generating numbers. """
        if self.remaining_quota < QUOTA_LIMIT:
            raise RandomOrgQuotaExceeded(self.remaining_quota)

    def random(self) -> float:
        """ Generate a random float by using integers as its fractional part.

        [06, 11, 21] => 0.061121
        """
        number_of_digits = RandintsToFloatOptions.RANDINTS_NUMBER_OF_DIGITS
        max_int = int('9' * number_of_digits)

        randints = self.randint(0, max_int, RandintsToFloatOptions.RANDINTS_QUANTITY)
        zero_padded_ints = (str(randint).zfill(number_of_digits) for randint in randints)
        return float(f"0.{''.join(zero_padded_ints)}")

    def randint(self, a: int, b: int, n: int = 1) -> Union[List[int], int]:
        """ Generates n integers at once as a list if n > 1 or as a single integer if n = 1. """
        params = {RandintRequestFields.RANDOMIZATION: RandintRequestFields.TRULY_RANDOM,
                  RandintRequestFields.BASE: RandintRequestFields.BASE_10,
                  RandintRequestFields.MIN: a, RandintRequestFields.MAX: b,
                  RandintRequestFields.NUM: n, RandintRequestFields.COL: 1}
        numbers = self._get_random_response(INTEGER_URL, params=params)

        integers = [int(random) for random in numbers.splitlines()]

        return integers if n > 1 else integers[0]

    @staticmethod
    def _get_text_response(url: str, params: Optional[Dict] = None) -> str:
        params = params or {}
        response = get(url, params={FORMAT: PLAIN_FORMAT, **params})
        response.raise_for_status()

        return response.text

    def _get_random_response(self, *args, **kwargs) -> str:
        self.check_quota()
        return self._get_text_response(*args, **kwargs)
