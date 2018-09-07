from enum import Enum
from random import Random
from typing import List, Dict, Optional

from requests import get


RANDOM_ORG_URL = 'https://www.random.org'
QUOTA_URL = f'{RANDOM_ORG_URL}/quota'
INTEGER_URL = f'{RANDOM_ORG_URL}/integers'

QUOTA_LIMIT = 0
MAX_QUOTA = 1_000_000

FORMAT = 'format'
PLAIN_FORMAT = 'plain'


class RandnumOptions(Enum):
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
    """ Random number generator powered by random.org.

    Provides the random.Random interface. You should call randints instead of calling randint
    multiple times in order to minimize the number of requests you make.
    """
    def __init__(self):
        quota = self._get_text_response(QUOTA_URL)

        self.remaining_quota = int(quota)
        super().__init__()

    def check_quota(self):
        """ Verify the user's IP can make requests. Should be called before generating numbers. """
        if self.remaining_quota < QUOTA_LIMIT:
            raise RandomOrgQuotaExceeded(self.remaining_quota)

    def random(self) -> float:
        raise NotImplementedError

    def randint(self, a: int, b: int) -> int:
        return self.randints(a, b, 1)[0]

    def randints(self, a: int, b: int, n: int) -> List[int]:
        """ Same as randint, but generates n numbers at once. """
        params = {RandnumOptions.RANDOMIZATION: RandnumOptions.TRULY_RANDOM,
                  RandnumOptions.BASE: RandnumOptions.BASE_10,
                  RandnumOptions.MIN: a, RandnumOptions.MAX: b,
                  RandnumOptions.NUM: n, RandnumOptions.COL: 1}
        numbers = self._get_random_response(INTEGER_URL, params=params)

        return [int(random) for random in numbers.splitlines()]

    @staticmethod
    def _get_text_response(url: str, params: Optional[Dict] = None) -> str:
        params = params or {}
        response = get(url, params={FORMAT: PLAIN_FORMAT, **params})
        response.raise_for_status()

        return response.text

    def _get_random_response(self, *args, **kwargs) -> str:
        self.check_quota()
        return self._get_text_response(*args, **kwargs)
